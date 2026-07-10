import os
import logging
import requests
from pydub import AudioSegment
import config

logger = logging.getLogger(__name__)

def gerar_audio_com_fundo(texto: str, caminho_saida: str) -> bool:
    """
    Gera a voz do locutor através da API do Speechify e sobrepõe 
    uma música de fundo suave utilizando pydub.
    """
    caminho_voz_pura = "temp_voz_pura.mp3"
    caminho_trilha_fundo = "assets/musica_fundo_suave.mp3"
    
    # Pegando a chave da API a partir das configurações ou variáveis de ambiente
    api_key = os.getenv("SPEECHIFY_API_KEY")
    
    if not api_key:
        logger.error("Chave 'SPEECHIFY_API_KEY' não encontrada nas variáveis de ambiente.")
        return False

    # 1. Requisição POST para a API do Speechify
    try:
        logger.info("Solicitando síntese de voz à API do Speechify...")
        
        url = "https://api.sws.speechify.com/v1/audio/speech"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "input": f"<speak>{texto}</speak>", # SSML para melhor controle de leitura se necessário
            "voice_id": "kristy",               # Substitua pelo ID da voz de sua preferência
            "audio_format": "mp3"
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code != 200:
            logger.error("Erro na API do Speechify (%s): %s", response.status_code, response.text)
            return False
            
        # Salva temporariamente a voz sem fundo
        with open(caminho_voz_pura, "wb") as f:
            f.write(response.content)
            
        logger.info("Áudio bruto do Speechify baixado com sucesso.")

    except Exception as erro:
        logger.error("Falha na comunicação com o Speechify: %s", erro)
        return False

    # 2. Mixagem da Voz com a Música de Fundo usando Pydub
    try:
        # Se você ainda não colocou uma música na pasta assets, ele salva apenas a voz pura como segurança
        if not os.path.exists(caminho_trilha_fundo):
            logger.warning("Trilha de fundo não encontrada em '%s'. Salvando apenas a voz.", caminho_trilha_fundo)
            os.rename(caminho_voz_pura, caminho_saida)
            return True

        logger.info("Iniciando a mixagem da trilha sonora com a voz do locutor...")
        
        # Carrega os arquivos de áudio
        audio_voz = AudioSegment.from_mp3(caminho_voz_pura)
        audio_trilha = AudioSegment.from_mp3(caminho_trilha_fundo)

        # Atenua o volume da música de fundo para -24dB para que ela não abafe a locução
        trilha_suave = audio_trilha - 24

        # Sobrepõe a voz por cima da trilha. O loop=True garante que a música recomece 
        # caso a fala do locutor seja mais longa que o arquivo de áudio da música.
        audio_final = trilha_suave.overlay(audio_voz, loop=True)

        # Corta o áudio final exatamente no tamanho da voz para não sobrar música tocando sozinha no fim
        audio_final = audio_final[:len(audio_voz)]

        # Exporta o arquivo final para a pasta de destino
        audio_final.export(caminho_saida, format="mp3")
        logger.info("Transmissão com música de fundo gerada com sucesso em: %s", caminho_saida)

        # Limpeza do arquivo temporário
        if os.path.exists(caminho_voz_pura):
            os.remove(caminho_voz_pura)

        return True

    except Exception as erro:
        logger.error("Erro crítico durante a mixagem do áudio: %s", erro)
        
        # Fallback: Se a mixagem quebrar por qualquer motivo, tenta salvar a voz pura para não perder a execução
        if os.path.exists(caminho_voz_pura):
            logger.info("Usando fallback: salvando áudio sem música de fundo.")
            os.rename(caminho_voz_pura, caminho_saida)
            return True
            
        return False