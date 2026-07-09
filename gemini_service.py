"""
gemini_service.py
Todas as chamadas ao Gemini: escolher o tema/artistas do dia (Diretor Musical)
e escrever as falas do locutor Saturn, já sabendo o que vai tocar.
"""

import json
import logging
import time
from pathlib import Path

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


def _chamar_gemini(prompt: str, tentativas: int = 3, espera_s: int = 4) -> str | None:
    """Wrapper com retry simples para chamadas de texto ao Gemini."""
    client = _get_client()
    for tentativa in range(1, tentativas + 1):
        try:
            resposta = client.models.generate_content(
                model=config.GEMINI_MODEL,
                contents=prompt,
            )
            if resposta.text:
                return resposta.text.strip()
            logger.warning("Resposta vazia do Gemini (tentativa %s/%s)", tentativa, tentativas)
        except Exception as erro:
            logger.warning(
                "Erro ao chamar Gemini (tentativa %s/%s): %s", tentativa, tentativas, erro
            )
        time.sleep(espera_s)
    return None


def gerar_planejamento_do_dia() -> dict | None:
    """
    O Gemini age como Diretor Musical: escolhe tema, clima, gêneros e artistas
    do dia. Retorna um dict pronto para ser salvo em programas/AAAA-MM-DD.json.
    """
    template = _carregar_prompt("diretor_musical.txt")
    texto = _chamar_gemini(template)
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
    """
    Gera o texto que o Saturn vai falar em um bloco específico.
    Se contexto_playlist for passado, o locutor menciona as próximas músicas.
    """
    template = _carregar_prompt("locutor.txt")

    trecho_playlist = ""
    if contexto_playlist:
        lista_formatada = "\n".join(f"- {faixa}" for faixa in contexto_playlist)
        trecho_playlist = f"\nAs próximas músicas que vão tocar são:\n{lista_formatada}\n"

    prompt = template.format(
        instrucao_bloco=instrucao_bloco,
        trecho_playlist=trecho_playlist,
    )
    return _chamar_gemini(prompt)
