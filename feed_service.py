"""
feed_service.py
Mantém o podcast.xml (RSS 2.0 + tags iTunes) do podcast atualizado no Supabase.

Estratégia: episódios FIXOS (um por bloco, guid estável tipo "dj-bloco-1").
Todo dia, o áudio e o texto de cada bloco são regravados/sobrescritos, e o
item correspondente no XML é atualizado in-place (mesmo guid, mesma posição).
Não se cria episódio novo por dia — é sempre a mesma lista de 4 episódios.
"""

import logging
from datetime import datetime, timezone
from email.utils import format_datetime
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape

import config
import supabase_service

logger = logging.getLogger("feed_service")

ITUNES_NS = "http://www.itunes.com/dtds/podcast-1.0.dtd"
ET.register_namespace("itunes", ITUNES_NS)


def _criar_canal_vazio() -> ET.Element:
    # Não declarar xmlns:itunes manualmente aqui: ET.register_namespace já
    # cuida disso ao serializar, e declarar os dois juntos gera XML inválido
    # (atributo xmlns:itunes duplicado).
    rss = ET.Element("rss", {"version": "2.0"})
    channel = ET.SubElement(rss, "channel")

    ET.SubElement(channel, "title").text = config.FEED_TITLE
    ET.SubElement(channel, "link").text = config.FEED_LINK
    ET.SubElement(channel, "language").text = config.FEED_LANGUAGE
    ET.SubElement(channel, "description").text = config.FEED_DESCRIPTION

    if config.FEED_MANAGING_EDITOR:
        ET.SubElement(channel, "managingEditor").text = config.FEED_MANAGING_EDITOR

    ET.SubElement(channel, f"{{{ITUNES_NS}}}author").text = config.FEED_AUTHOR

    if config.FEED_OWNER_NAME or config.FEED_OWNER_EMAIL:
        owner = ET.SubElement(channel, f"{{{ITUNES_NS}}}owner")
        if config.FEED_OWNER_NAME:
            ET.SubElement(owner, f"{{{ITUNES_NS}}}name").text = config.FEED_OWNER_NAME
        if config.FEED_OWNER_EMAIL:
            ET.SubElement(owner, f"{{{ITUNES_NS}}}email").text = config.FEED_OWNER_EMAIL

    if config.FEED_IMAGE_URL:
        ET.SubElement(channel, f"{{{ITUNES_NS}}}image", {"href": config.FEED_IMAGE_URL})
        image = ET.SubElement(channel, "image")
        ET.SubElement(image, "url").text = config.FEED_IMAGE_URL
        ET.SubElement(image, "title").text = config.FEED_TITLE
        ET.SubElement(image, "link").text = config.FEED_LINK

    ET.SubElement(channel, f"{{{ITUNES_NS}}}summary").text = config.FEED_DESCRIPTION
    ET.SubElement(channel, f"{{{ITUNES_NS}}}explicit").text = config.FEED_EXPLICIT
    ET.SubElement(channel, f"{{{ITUNES_NS}}}type").text = config.FEED_TYPE
    ET.SubElement(channel, f"{{{ITUNES_NS}}}category", {"text": config.FEED_CATEGORY})

    return rss


def _carregar_feed_existente() -> ET.Element:
    """Baixa e faz parse do feed.xml atual. Se não existir ou estiver corrompido, cria um novo."""
    conteudo = supabase_service.baixar_arquivo(config.FEED_BUCKET, config.FEED_FILENAME)
    if not conteudo:
        logger.info("Nenhum feed.xml existente, criando um novo.")
        return _criar_canal_vazio()

    try:
        return ET.fromstring(conteudo)
    except ET.ParseError as erro:
        logger.error("feed.xml existente está corrompido (%s). Criando um novo do zero.", erro)
        return _criar_canal_vazio()


def _definir_texto(item: ET.Element, tag: str, texto: str) -> None:
    """Define o texto de uma subtag do item, criando-a se ainda não existir."""
    elemento = item.find(tag)
    if elemento is None:
        elemento = ET.SubElement(item, tag)
    elemento.text = texto


def _atualizar_item(
    item: ET.Element,
    titulo: str,
    descricao: str,
    url_audio: str,
    tamanho_bytes: int,
    data_publicacao: datetime,
) -> None:
    """Atualiza os campos de um <item> já existente, sem trocar seu <guid>."""
    _definir_texto(item, "title", titulo)
    _definir_texto(item, "description", escape(descricao))
    _definir_texto(item, "pubDate", format_datetime(data_publicacao))

    enclosure = item.find("enclosure")
    if enclosure is None:
        enclosure = ET.SubElement(item, "enclosure")
    enclosure.set("url", url_audio)
    enclosure.set("length", str(tamanho_bytes))
    enclosure.set("type", "audio/mpeg")


def _criar_item(guid: str, **kwargs) -> ET.Element:
    item = ET.Element("item")
    ET.SubElement(item, "guid", {"isPermaLink": "false"}).text = guid
    _atualizar_item(item, **kwargs)
    return item


def atualizar_episodios(blocos: list[dict]) -> bool:
    """
    blocos: lista de dicts com as chaves:
        - numero_bloco (int)
        - titulo (str)
        - descricao (str)       -> pode ser o próprio roteiro do Saturn
        - nome_arquivo_nuvem (str)
        - tamanho_bytes (int)

    Para cada bloco, encontra o <item> com guid "{FEED_GUID_PREFIX}-{numero_bloco}"
    e atualiza seus campos in-place. Se o item ainda não existir no feed, cria.
    Nunca acumula: o feed sempre tem exatamente um episódio por bloco.
    """
    rss = _carregar_feed_existente()
    channel = rss.find("channel")
    if channel is None:
        logger.error("Estrutura de podcast.xml inesperada: tag <channel> não encontrada.")
        return False

    agora = datetime.now(timezone.utc)

    # Indexa os itens existentes por guid pra localizar rápido o que atualizar.
    itens_por_guid = {}
    for item in channel.findall("item"):
        guid_elemento = item.find("guid")
        if guid_elemento is not None and guid_elemento.text:
            itens_por_guid[guid_elemento.text.strip()] = item

    atualizados, criados = 0, 0

    for bloco in blocos:
        guid = f"{config.FEED_GUID_PREFIX}-{bloco['numero_bloco']}"
        url_audio = supabase_service.url_publica(config.FEED_BUCKET, bloco["nome_arquivo_nuvem"])

        campos = dict(
            titulo=bloco["titulo"],
            descricao=bloco.get("descricao", ""),
            url_audio=url_audio,
            tamanho_bytes=bloco.get("tamanho_bytes", 0),
            data_publicacao=agora,
        )

        item_existente = itens_por_guid.get(guid)
        if item_existente is not None:
            _atualizar_item(item_existente, **campos)
            atualizados += 1
        else:
            novo_item = _criar_item(guid, **campos)
            channel.append(novo_item)
            criados += 1

    xml_final = ET.tostring(rss, encoding="unicode")
    xml_final = '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_final

    sucesso = supabase_service.upload_texto(
        config.FEED_BUCKET, config.FEED_FILENAME, xml_final, "application/rss+xml"
    )
    if sucesso:
        logger.info(
            "podcast.xml atualizado: %s episódio(s) sobrescrito(s), %s criado(s).",
            atualizados,
            criados,
        )
    return sucesso
