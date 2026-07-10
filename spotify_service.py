"""
spotify_service.py
Busca e monta a playlist do dia com base nos artistas escolhidos pelo Gemini.
Não usa mais audio_features()/BPM, pois esse endpoint foi restrito pelo
Spotify para novos apps e não é mais confiável.
"""

import logging
import random

import spotipy
from spotipy.oauth2 import SpotifyOAuth

import config

logger = logging.getLogger("spotify_service")

_sp = None


def _get_client() -> spotipy.Spotify:
    global _sp
    if _sp is None:
        _sp = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                client_id=config.SPOTIFY_CLIENT_ID,
                client_secret=config.SPOTIFY_CLIENT_SECRET,
                redirect_uri=config.SPOTIFY_REDIRECT_URI,
                scope="playlist-modify-public playlist-modify-private user-top-read",
            )
        )
    return _sp


def buscar_faixas_por_artista(nome_artista: str, limite: int = None) -> list[dict]:
    limite = limite or config.FAIXAS_POR_ARTISTA
    sp = _get_client()
    try:
        resultado = sp.search(q=f'artist:"{nome_artista}"', type="track", limit=10)
        faixas = resultado["tracks"]["items"]
    except Exception as erro:
        logger.warning("Falha ao buscar faixas de '%s': %s", nome_artista, erro)
        return []

    if not faixas:
        logger.warning("Nenhuma faixa encontrada para '%s'.", nome_artista)
        return []

    random.shuffle(faixas)
    escolhidas = faixas[:limite]

    bpm_map = {}
    try:
        track_ids = [faixa["id"] for faixa in escolhidas]
        if track_ids:
            for feat in filter(None, features):
                bpm_map[feat["id"]] = feat["tempo"]
    except Exception as erro:
        logger.warning("Falha ao buscar detalhes de áudio (BPM) para '%s': %s", nome_artista, erro)

    return [
        {
            "name": faixa["name"],
            "artist": faixa["artists"][0]["name"],
            "uri": faixa["uri"],
            "bpm": int(bpm_map.get(faixa["id"], 120)) 
        }
        for faixa in escolhidas
    ]


def montar_playlist_do_dia(artistas: list[str]) -> list[dict]:

    playlist: list[dict] = []
    artistas_usados = set()

    for artista in artistas:
        if len(playlist) >= config.TAMANHO_PLAYLIST:
            break
        if artista.lower() in artistas_usados:
            continue

        faixas = buscar_faixas_por_artista(artista)
        if faixas:
            playlist.extend(faixas)
            artistas_usados.add(artista.lower())
            logger.info("Adicionadas %s faixa(s) de %s", len(faixas), artista)

    playlist = playlist[: config.TAMANHO_PLAYLIST]

    playlist.sort(key=lambda faixa: faixa.get("bpm", 120))
    
    logger.info("Playlist reordenada por BPM com sucesso para a transmissão.")

    return playlist

def atualizar_playlist(faixas: list[dict]) -> bool:
    """Substitui as faixas da playlist alvo no Spotify pelas faixas do dia (só música)."""
    uris = [faixa["uri"] for faixa in faixas]
    return atualizar_playlist_com_uris(uris)


def atualizar_playlist_com_uris(uris: list[str]) -> bool:
    """
    Substitui os itens da playlist por uma lista de URIs já pronta — pode
    misturar spotify:track:... e spotify:episode:....
    """
    sp = _get_client()
    if not uris:
        logger.error("Lista de URIs vazia, não é possível atualizar a playlist.")
        return False

    try:
        sp.playlist_replace_items(config.PLAYLIST_ID, uris)
        logger.info("Playlist do Spotify atualizada com %s item(ns).", len(uris))
        return True
    except Exception as erro:
        logger.error("Erro ao atualizar playlist no Spotify: %s", erro)
        return False


def buscar_episodios_do_show(show_id: str) -> list[dict]:
    """Busca todos os episódios do show (paginando), usado pra achar os URIs dos blocos."""
    sp = _get_client()
    episodios: list[dict] = []
    try:
        pagina = sp.show_episodes(show_id, limit=50, market="BR")
    except Exception as erro:
        logger.error("Falha ao buscar episódios do show '%s': %s", show_id, erro)
        return []

    while pagina:
        episodios.extend(item for item in pagina.get("items", []) if item)
        if pagina.get("next"):
            pagina = sp.next(pagina)
        else:
            break

    return episodios


def mapear_episodios_por_bloco(show_id: str, numeros_bloco: list[int]) -> dict[int, str]:
    """
    Casa cada número de bloco com o URI do episódio correspondente no Spotify,
    procurando 'bloco {n}' no nome do episódio (o título muda de dia pra dia,
    mas sempre contém esse trecho — ver feed_service.py).
    """
    episodios = buscar_episodios_do_show(show_id)
    mapa: dict[int, str] = {}

    for numero in numeros_bloco:
        alvo = f"bloco {numero}"
        encontrado = next(
            (ep for ep in episodios if alvo in ep.get("name", "").lower()), None
        )
        if encontrado:
            mapa[numero] = encontrado["uri"]
        else:
            logger.warning(
                "Episódio do bloco %s ainda não encontrado no show do Spotify "
                "(pode levar um tempo pro Spotify reindexar depois do submit).",
                numero,
            )

    return mapa


def montar_sequencia_intercalada(
    faixas_musicas: list[dict], mapa_episodios_por_bloco: dict[int, str]
) -> list[str]:
    """
    Monta a ordem final: bloco1 -> 1/3 das músicas -> bloco2 -> 1/3 -> bloco3
    -> 1/3 -> bloco4. Se faltar o URI de algum bloco, ele simplesmente é
    pulado (a playlist sai só com os blocos que já existem no Spotify).
    """
    uris_musicas = [faixa["uri"] for faixa in faixas_musicas]
    n = len(uris_musicas)
    partes = 3
    tamanho_parte = n // partes if partes else 0

    blocos_musica = []
    for i in range(partes):
        inicio = i * tamanho_parte
        fim = (i + 1) * tamanho_parte if i < partes - 1 else n
        blocos_musica.append(uris_musicas[inicio:fim])

    sequencia: list[str] = []
    for numero_bloco in range(1, 5):
        uri_episodio = mapa_episodios_por_bloco.get(numero_bloco)
        if uri_episodio:
            sequencia.append(uri_episodio)
        if numero_bloco <= 3:
            sequencia.extend(blocos_musica[numero_bloco - 1])

    return sequencia
