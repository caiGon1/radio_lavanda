"""
tts_service.py
Converte o roteiro do Saturn em áudio usando edge-tts (voz neural gratuita).
"""

import asyncio
import logging

import edge_tts

import config

logger = logging.getLogger("tts_service")


async def _gerar_audio_async(texto: str, caminho_saida: str, voz: str) -> None:
    comunicador = edge_tts.Communicate(texto, voz)
    await comunicador.save(caminho_saida)


def gerar_audio(texto: str, caminho_saida: str, voz: str = None) -> bool:
    """Versão síncrona, pronta para ser chamada do restante do pipeline."""
    voz = voz or config.TTS_VOICE
    try:
        asyncio.run(_gerar_audio_async(texto, caminho_saida, voz))
        return True
    except Exception as erro:
        logger.error("Falha ao gerar áudio TTS: %s", erro)
        return False
