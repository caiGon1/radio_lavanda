"""
config.py
Centraliza a leitura de todas as credenciais e parâmetros do projeto.
Nunca coloque chaves direto no código — tudo vem do arquivo .env.
"""

import os
import logging
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Credenciais
# ---------------------------------------------------------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BUCKET_NAME = os.getenv("BUCKET_NAME", "radio-lavanda-audios")

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8888/callback")
PLAYLIST_ID = os.getenv("PLAYLIST_ID")


SPEECHIFY_API_KEY = os.getenv("SPEECHIFY_API_KEY")
ELEVENLABS_API_KEY=os.getenv("ELEVENLABS_API_KEY")


# ID do "Show" (podcast) no catálogo do Spotify. Só existe DEPOIS que você
# submete o podcast.xml via Spotify for Podcasters e o Spotify aprova/ingere
# o feed. Enquanto vazio, a playlist recebe só música (comportamento atual).
SPOTIFY_SHOW_ID = os.getenv("SPOTIFY_SHOW_ID", "")

TTS_VOICE = os.getenv("TTS_VOICE", "pt-BR-AntonioNeural")

# Quantas faixas buscar por artista e quantas entram na playlist final
FAIXAS_POR_ARTISTA = int(os.getenv("FAIXAS_POR_ARTISTA", 2))
TAMANHO_PLAYLIST = int(os.getenv("TAMANHO_PLAYLIST", 16))

PASTA_PROGRAMAS = os.getenv("PASTA_PROGRAMAS", "programas")
PASTA_PROMPTS = os.getenv("PASTA_PROMPTS", "prompts")

# ---------------------------------------------------------------------------
# Feed RSS do podcast
# ---------------------------------------------------------------------------
# Assume que BUCKET_NAME é público no Supabase Storage. Se não for, as URLs
# geradas não vão funcionar em apps de podcast (Spotify, Apple Podcasts etc).
# ---------------------------------------------------------------------------
# Feed RSS do podcast
# ---------------------------------------------------------------------------
# Assume que BUCKET_NAME é público no Supabase Storage. Se não for, as URLs
# geradas não vão funcionar em apps de podcast (Spotify, Apple Podcasts etc).
FEED_BUCKET = os.getenv("FEED_BUCKET", BUCKET_NAME)
FEED_FILENAME = os.getenv("FEED_FILENAME", "podcast.xml")

FEED_TITLE = os.getenv("FEED_TITLE", "Minha Rádio AI Particular")
FEED_LINK = os.getenv("FEED_LINK", "https://meusite.com")
FEED_DESCRIPTION = os.getenv("FEED_DESCRIPTION", "Uma rádio automatizada usando IA.")
FEED_LANGUAGE = os.getenv("FEED_LANGUAGE", "pt-BR")
FEED_AUTHOR = os.getenv("FEED_AUTHOR", "AI Agent DJ")
FEED_MANAGING_EDITOR = os.getenv("FEED_MANAGING_EDITOR", "")
FEED_OWNER_NAME = os.getenv("FEED_OWNER_NAME", FEED_AUTHOR)
FEED_OWNER_EMAIL = os.getenv("FEED_OWNER_EMAIL", FEED_MANAGING_EDITOR)
FEED_IMAGE_URL = os.getenv("FEED_IMAGE_URL", "")
FEED_EXPLICIT = os.getenv("FEED_EXPLICIT", "false")
FEED_TYPE = os.getenv("FEED_TYPE", "episodic")
FEED_CATEGORY = os.getenv("FEED_CATEGORY", "Music")

# Prefixo do guid de cada bloco. Usa o mesmo padrão do podcast.xml original
# ("dj-bloco-1", "dj-bloco-2"...) pra que o update in-place encontre e
# sobrescreva exatamente os itens que já existem, em vez de criar novos.
FEED_GUID_PREFIX = os.getenv("FEED_GUID_PREFIX", "dj-bloco")

# ---------------------------------------------------------------------------
# Validação
# ---------------------------------------------------------------------------
_REQUIRED = {
    "GEMINI_API_KEY": GEMINI_API_KEY,
    "SUPABASE_URL": SUPABASE_URL,
    "SUPABASE_KEY": SUPABASE_KEY,
    "SPOTIFY_CLIENT_ID": SPOTIFY_CLIENT_ID,
    "SPOTIFY_CLIENT_SECRET": SPOTIFY_CLIENT_SECRET,
    "PLAYLIST_ID": PLAYLIST_ID,
}


def validar_config() -> None:
    """Levanta um erro claro se alguma variável obrigatória estiver faltando."""
    faltando = [nome for nome, valor in _REQUIRED.items() if not valor]
    if faltando:
        raise EnvironmentError(
            "Variáveis de ambiente obrigatórias ausentes no .env: "
            + ", ".join(faltando)
        )


# ---------------------------------------------------------------------------
# Logging padrão do projeto
# ---------------------------------------------------------------------------
def configurar_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )
