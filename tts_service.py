import os
import logging
from pydub import AudioSegment
from elevenlabs.client import ElevenLabs  # Import oficial da ElevenLabs
import config

logger = logging.getLogger(__name__)

def gerar_audio_com_fundo(texto: str, caminho_saida: str) -> bool:
    caminho_voz_pura = "temp_voz_pura.mp3"
    caminho_trilha_fundo = "assets/musica_fundo_suave.mp3"
    
    # 1. Geração de voz usando a API da ElevenLabs
    try:
        logger.info("Solicitando síntese de voz à API da ElevenLabs...")
        
        # Inicializa o cliente com a chave da variável de ambiente
        client = ElevenLabs(
            api_key=os.getenv("ELEVENLABS_API_KEY"),
        )
        
        # O método convert retorna um generator de bytes
        audio_generator = client.text_to_speech.convert(
            text=texto,
            voice_id="CwhRBWXzGAHq8TQ4Fs17",  
            model_id="eleven_v3",
              language_code="pt",
            output_format="mp3_44100_128"
           
        )
        
        # Salva os bytes recebidos em um arquivo MP3 válido
        with open(caminho_voz_pura, "wb") as f:
            for chunk in audio_generator:
                if chunk:
                    f.write(chunk)
                    
        logger.info("Áudio bruto gerado e salvo com sucesso.")

    except Exception as erro:
        logger.error("Falha na comunicação com a ElevenLabs: %s", erro)
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