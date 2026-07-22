"""
radio.py
Orquestra o fluxo completo do dia:

Gemini escolhe tema/artistas -> Spotify busca musicas -> remove artistas
repetidos -> Spotify atualiza playlist -> Saturn le a playlist -> Gemini
escreve as falas -> Edge-TTS gera audios -> Supabase envia tudo.
"""

import json
import logging
import os
from datetime import date
from pathlib import Path

import config
import gemini_service
import spotify_service
import tts_service
import supabase_service
import feed_service

logger = logging.getLogger("radio")


BLOCOS_CONFIG = {
    1: (
        "Abertura do show. Se apresente, convide os ouvintes a curtirem a Rádio Lavanda, "
        "apresente o tema e o clima do programa de hoje e fale o que eles podem esperar do bloco."
    ),
    2: (
        "Transição 1. Traga uma curiosidade musical rápida sobre os artistas ou faixas que vão tocar, "
        "aproveitando os fatos da web fornecidos. Mantenha o tom leve, descontraído e conectado ao tema do dia."
    ),
    3: (
        "Transição 2. Faça uma reflexão profunda, mas aconchegante, sobre a vida e convide o ouvinte "
        "a estar presente no momento. Relacione essa reflexão com a vibe da rádio e o clima do dia."
    ),
    4: (
        "Encerramento. Agradeça os ouvintes por ouvirem a Rádio Lavanda, "
        "deseje um ótimo dia/noite e chame o último bloco musical caso ainda tenha."
    ),
}


def _salvar_planejamento(planejamento: dict, playlist: list[dict]) -> Path:
    Path(config.PASTA_PROGRAMAS).mkdir(parents=True, exist_ok=True)
    caminho = Path(config.PASTA_PROGRAMAS) / f"{date.today().isoformat()}.json"

    dados = {
        **planejamento,
        "playlist": playlist,
    }
    caminho.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Planejamento do dia salvo em %s", caminho)
    return caminho


def _gerar_blocos_de_audio(playlist: list[dict]) -> list[dict]:
    """Gera, sobe (sobrescrevendo) e retorna os metadados de cada bloco pro feed RSS."""
    nomes_faixas = [f"{f['name']} — {f['artist']}" for f in playlist]
    hoje_str = date.today().strftime("%d/%m/%Y")
    blocos_publicados = []

    for numero_bloco, instrucao in BLOCOS_CONFIG.items():
        logger.info("Processando bloco %s...", numero_bloco)

        # Só passa o contexto da playlist nos blocos de abertura e encerramento,
        # que são onde faz sentido o locutor "chamar" as próximas músicas.
        contexto = nomes_faixas[:4] if numero_bloco in (1, 4) else None

        roteiro = gemini_service.gerar_fala_bloco(instrucao, contexto_playlist=contexto)
        if not roteiro:
            logger.error("Pulando bloco %s: não foi possível gerar o roteiro.", numero_bloco)
            continue

        # Nome de arquivo FIXO (sem data): o objetivo é sobrescrever o mesmo
        # episódio todo dia, não acumular um histórico.
        nome_arquivo_local = f"temp_bloco_{numero_bloco}.mp3"
        sucesso_audio = tts_service.gerar_audio_com_fundo(roteiro, nome_arquivo_local)
        if not sucesso_audio:
            logger.error("Pulando bloco %s: falha na geração de áudio.", numero_bloco)
            continue

        tamanho_bytes = os.path.getsize(nome_arquivo_local)
        nome_arquivo_nuvem = f"bloco_{numero_bloco}.mp3"

        sucesso_upload = supabase_service.upload_audio(nome_arquivo_local, nome_arquivo_nuvem)
        if os.path.exists(nome_arquivo_local):
            os.remove(nome_arquivo_local)

        if not sucesso_upload:
            logger.error("Pulando bloco %s no feed: falha no upload.", numero_bloco)
            continue

        blocos_publicados.append(
            {
                "numero_bloco": numero_bloco,
                "titulo": f"Rádio Lavanda — {hoje_str} — Bloco {numero_bloco}",
                "descricao": roteiro,
                "nome_arquivo_nuvem": nome_arquivo_nuvem,
                "tamanho_bytes": tamanho_bytes,
            }
        )

    return blocos_publicados


def executar_dia() -> None:
    config.configurar_logging()
    config.validar_config()

    logger.info("Iniciando programação diária da Rádio Lavanda...")

    # 1. Gemini escolhe o tema do dia e os artistas
    planejamento = gemini_service.gerar_planejamento_do_dia()
    if not planejamento:
        logger.error("Não foi possível gerar o planejamento do dia. Abortando.")
        return
    logger.info("Tema de hoje: %s (%s)", planejamento["tema"], planejamento["clima"])

    # 2/3. Spotify busca músicas e remove artistas repetidos
    playlist = spotify_service.montar_playlist_do_dia(planejamento["artistas"])
    if not playlist:
        logger.error("Nenhuma faixa encontrada para os artistas escolhidos. Abortando.")
        return

    # 4. Spotify atualiza a playlist
    spotify_service.atualizar_playlist(playlist)

    # Salva o planejamento + playlist final para auditoria/reuso
    _salvar_planejamento(planejamento, playlist)

    # 5/6/7. Saturn "lê" a playlist, Gemini escreve as falas, Edge-TTS gera os áudios
    blocos_publicados = _gerar_blocos_de_audio(playlist)

    # 8. Cada bloco ATUALIZA (não cria) seu episódio fixo no podcast.xml
    if blocos_publicados:
        feed_service.atualizar_episodios(blocos_publicados)
    else:
        logger.warning("Nenhum bloco foi publicado hoje, podcast.xml não foi atualizado.")

    # 9. (Opcional) Se o show já está publicado no Spotify, intercala os
    # episódios do Saturn com a música na mesma playlist. Só roda se
    # SPOTIFY_SHOW_ID estiver preenchido no .env.
    if config.SPOTIFY_SHOW_ID and blocos_publicados:
        numeros_bloco = [b["numero_bloco"] for b in blocos_publicados]
        mapa_episodios = spotify_service.mapear_episodios_por_bloco(
            config.SPOTIFY_SHOW_ID, numeros_bloco
        )
        if mapa_episodios:
            sequencia = spotify_service.montar_sequencia_intercalada(playlist, mapa_episodios)
            spotify_service.atualizar_playlist_com_uris(sequencia)
        else:
            logger.warning(
                "Nenhum episódio encontrado no show do Spotify ainda; "
                "playlist ficou só com música."
            )

    logger.info("Transmissão diária da Rádio Lavanda pronta! ✅")


if __name__ == "__main__":
    executar_dia()
