"""
bpm_service.py
Busca o BPM real das faixas via ReccoBeats (substituto do audio_features()
do Spotify, restrito desde nov/2024 pra apps novos). Guarda cache local em
JSON pra evitar bater na API toda vez que a mesma faixa aparecer de novo.
"""

import json
import logging
from pathlib import Path

import requests

logger = logging.getLogger("bpm_service")

RECCOBEATS_BASE = "https://api.reccobeats.com/v1"
CACHE_PATH = Path(__file__).parent / "cache" / "bpm_cache.json"
TIMEOUT = 6


def _carregar_cache() -> dict:
    if CACHE_PATH.exists():
        try:
            return json.loads(CACHE_PATH.read_text())
        except Exception:
            return {}
    return {}


def _salvar_cache(cache: dict) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache))


def _resolver_id_reccobeats(spotify_track_id: str) -> str | None:
    try:
        resp = requests.get(
            f"{RECCOBEATS_BASE}/track",
            params={"ids": spotify_track_id},
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        dados = resp.json().get("content", [])
        if dados:
            return dados[0]["id"]
    except Exception as erro:
        logger.warning("ReccoBeats: falha ao resolver ID de '%s': %s", spotify_track_id, erro)
    return None


def _buscar_tempo(reccobeats_id: str) -> float | None:
    try:
        resp = requests.get(
            f"{RECCOBEATS_BASE}/track/{reccobeats_id}/audio-features",
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json().get("tempo")
    except Exception as erro:
        logger.warning("ReccoBeats: falha ao buscar tempo de '%s': %s", reccobeats_id, erro)
    return None


def obter_bpm(spotify_track_id: str) -> int | None:
    """BPM real da faixa (cacheado). Retorna None se não conseguir resolver."""
    cache = _carregar_cache()
    if spotify_track_id in cache:
        return cache[spotify_track_id]

    bpm = None
    reccobeats_id = _resolver_id_reccobeats(spotify_track_id)
    if reccobeats_id:
        tempo = _buscar_tempo(reccobeats_id)
        if tempo:
            bpm = round(tempo)

    cache[spotify_track_id] = bpm  # cacheia até o None, pra não retentar sempre
    _salvar_cache(cache)
    return bpm