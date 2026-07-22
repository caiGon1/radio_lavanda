"""
gemini_service.py
Todas as chamadas ao Gemini: escolher o tema/artistas do dia (Diretor Musical)
e escrever as falas do locutor Saturn, já sabendo o que vai tocar.
"""

import json
import logging
import time
from pathlib import Path

from duckduckgo_search import DDGS
from google import genai

import config

logger = logging.getLogger("gemini_service")

_client = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=config.GEMINI_API_KEY)
    return _client


def _carregar_prompt(nome_arquivo: str) -> str:
    caminho = Path(config.PASTA_PROMPTS) / nome_arquivo
    return caminho.read_text(encoding="utf-8")


def buscar_contexto_duckduckgo(termo: str, max_resultados: int = 3) -> str:
    """
    Busca notícias/dados recentes via DuckDuckGo para alimentar o contexto do prompt.
    """
    try:
        with DDGS() as ddgs:
            resultados = list(ddgs.news(keywords=termo, region="wt-wt", max_results=max_resultados))
            
            if not resultados:
                resultados = list(ddgs.text(keywords=termo, region="wt-wt", max_results=max_resultados))

        contextos = []
        for r in resultados:
            titulo = r.get("title", "")
            snippet = r.get("body") or r.get("snippet") or ""
            if titulo or snippet:
                contextos.append(f"- {titulo}: {snippet}")
        
        return "\n".join(contextos)
    except Exception as e:
        logger.warning("Falha ao buscar dados no DuckDuckGo para '%s': %s", termo, e)
        return ""


def _chamar_gemini(prompt: str, tentativas: int = 3, espera_s: int = 4) -> str | None:
    """Wrapper com retry para chamadas de texto ao Gemini."""
    client = _get_client()

    for tentativa in range(1, tentativas + 1):
        try:
            resposta = client.models.generate_content(
                model=config.GEMINI_MODEL,
                contents=prompt,
            )
            if resposta.text:
                return resposta.text.strip()
            logger.warning(
                "Resposta vazia do Gemini (tentativa %s/%s)",
                tentativa,
                tentativas,
            )
        except Exception as erro:
            logger.warning(
                "Erro ao chamar Gemini (tentativa %s/%s): %s",
                tentativa,
                tentativas,
                erro,
            )
        time.sleep(espera_s)
    return None


def gerar_planejamento_do_dia() -> dict | None:
    contexto_web = buscar_contexto_duckduckgo("culture news music trends", max_resultados=4)
    if not contexto_web:
        contexto_web = "Nenhuma notícia relevante encontrada. Siga com base no clima atual da estação."

    template = _carregar_prompt("diretor_musical.txt")
    
    # Substituição segura sem f-string/format caso o prompt tenha outras chaves
    prompt_final = template.replace("{contexto_web}", contexto_web)

    texto = _chamar_gemini(prompt_final)
    if not texto:
        logger.error("Não foi possível gerar o planejamento do dia.")
        return None

    texto_limpo = texto.replace("```json", "").replace("```", "").strip()
    try:
        planejamento = json.loads(texto_limpo)
    except json.JSONDecodeError as erro:
        logger.error("JSON inválido retornado pelo Gemini: %s\nConteúdo: %s", erro, texto)
        return None

    obrigatorios = {"tema", "clima", "generos", "artistas"}
    if not obrigatorios.issubset(planejamento.keys()):
        logger.error("Planejamento incompleto, faltam campos: %s", obrigatorios - planejamento.keys())
        return None

    return planejamento


def gerar_fala_bloco(instrucao_bloco: str, contexto_playlist: list[str] | None = None) -> str | None:
    template = _carregar_prompt("locutor.txt")

    trecho_playlist = ""
    info_extra = ""

    if contexto_playlist:
        lista_formatada = "\n".join(f"- {faixa}" for faixa in contexto_playlist)
        trecho_playlist = f"\nAs próximas músicas que vão tocar são:\n{lista_formatada}\n"
        
        primeiro_item = contexto_playlist[0]
        contexto_pesquisa = buscar_contexto_duckduckgo(primeiro_item, max_resultados=2)
        if contexto_pesquisa:
            info_extra = f"\nCuriosidades/Notícias da web para enriquecer a fala sobre os artistas:\n{contexto_pesquisa}\n"

    # Usando .replace() direto em vez de .format() para evitar KeyError com colchetes/chaves do prompt
    bloco_completo = f"{trecho_playlist}{info_extra}"
    prompt = template.replace("{instrucao_bloco}", instrucao_bloco).replace("{trecho_playlist}", bloco_completo)

    return _chamar_gemini(prompt)