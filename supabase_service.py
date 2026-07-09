"""
supabase_service.py
Upload dos blocos de áudio gerados para o bucket do Supabase Storage.
"""

import logging

from supabase import create_client, Client

import config

logger = logging.getLogger("supabase_service")

_supabase: Client = None


def _get_client() -> Client:
    global _supabase
    if _supabase is None:
        _supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
    return _supabase


def url_publica(bucket: str, nome_arquivo_nuvem: str) -> str:
    """Monta a URL pública padrão do Supabase Storage. Só funciona se o bucket for público."""
    supabase = _get_client()
    return supabase.storage.from_(bucket).get_public_url(nome_arquivo_nuvem)


def baixar_arquivo(bucket: str, nome_arquivo_nuvem: str) -> bytes | None:
    """Baixa um arquivo do bucket. Retorna None se não existir ainda (ex: primeiro feed.xml)."""
    supabase = _get_client()
    try:
        return supabase.storage.from_(bucket).download(nome_arquivo_nuvem)
    except Exception as erro:
        logger.info("Arquivo '%s' ainda não existe no bucket '%s' (%s)", nome_arquivo_nuvem, bucket, erro)
        return None


def upload_texto(bucket: str, nome_arquivo_nuvem: str, conteudo: str, content_type: str) -> bool:
    """Sobe um arquivo de texto (ex: feed.xml), sobrescrevendo se já existir."""
    supabase = _get_client()
    try:
        supabase.storage.from_(bucket).upload(
            file=conteudo.encode("utf-8"),
            path=nome_arquivo_nuvem,
            file_options={"cache-control": "0", "upsert": "true", "content-type": content_type},
        )
        logger.info("Upload de texto concluído: %s/%s", bucket, nome_arquivo_nuvem)
        return True
    except Exception as erro:
        logger.error("Falha no upload de texto (%s/%s): %s", bucket, nome_arquivo_nuvem, erro)
        return False


def upload_audio(caminho_local: str, nome_arquivo_nuvem: str) -> bool:
    """Envia um arquivo de áudio local para o bucket configurado, sobrescrevendo se já existir."""
    supabase = _get_client()
    try:
        with open(caminho_local, "rb") as f:
            audio_bytes = f.read()

        if not audio_bytes:
            logger.error("Arquivo de áudio vazio: %s", caminho_local)
            return False

        supabase.storage.from_(config.BUCKET_NAME).upload(
            file=audio_bytes,
            path=nome_arquivo_nuvem,
            file_options={"cache-control": "0", "upsert": "true", "content-type": "audio/mpeg"},
        )
        logger.info("Upload concluído: %s", nome_arquivo_nuvem)
        return True
    except Exception as erro:
        logger.error("Falha no upload para o Supabase (%s): %s", nome_arquivo_nuvem, erro)
        return False
