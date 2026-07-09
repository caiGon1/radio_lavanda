# Rádio Lavanda 🌿

DJ de rádio 100% automatizado: o Gemini atua como Diretor Musical e Roteirista,
o Spotify monta a playlist do dia, o Edge-TTS grava as falas do locutor
"Saturn" e o Supabase hospeda os áudios finais.

## Instalação

```bash
pip install -r requirements.txt
```

## Configuração

Todas as credenciais já estão em `.env` (as mesmas do protótipo original —
troque-as por chaves novas antes de subir isso para produção ou repositório
público, já que as antigas foram compartilhadas em texto puro).

## Uso

```bash
python main.py
```

Isso executa o fluxo completo do dia:

1. Gemini escolhe tema, clima, gêneros e artistas do dia.
2. Spotify busca faixas por artista (sem repetir artista).
3. A playlist do Spotify é atualizada.
4. O planejamento do dia + playlist final são salvos em `programas/AAAA-MM-DD.json`.
5. Gemini escreve as falas dos 4 blocos, já citando as próximas músicas.
6. Edge-TTS grava cada bloco em MP3.
7. Cada bloco é enviado para o bucket do Supabase.

## Agendamento

Para rodar todo dia automaticamente, agende `python main.py` via cron
(Linux/Mac) ou Task Scheduler (Windows), por exemplo às 06h:

```
0 6 * * * cd /caminho/do/projeto && /usr/bin/python3 main.py >> log.txt 2>&1
```

## Estrutura

```
radio_lavanda/
├── main.py              # ponto de entrada
├── config.py             # credenciais e parâmetros (lidos do .env)
├── radio.py               # orquestrador do fluxo diário
├── spotify_service.py     # busca e atualização da playlist
├── gemini_service.py      # diretor musical + roteirista
├── tts_service.py         # texto -> áudio (edge-tts)
├── supabase_service.py    # upload dos áudios
├── prompts/                # prompts do Gemini, separados do código
└── programas/               # histórico diário em JSON (auditoria)
```

## Próximos passos sugeridos

- Trocar as credenciais do `.env` (Gemini, Supabase, Spotify) — as atuais já
  foram expostas em texto puro e devem ser consideradas comprometidas.
- Adicionar testes automatizados para `spotify_service` e `gemini_service`.
- Persistir o histórico de artistas dos últimos N dias para evitar repetição
  entre dias, não só dentro do mesmo dia.
