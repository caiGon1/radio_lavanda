"""
main.py
Ponto de entrada. Rode `python main.py` (idealmente agendado via cron / task
scheduler) para gerar a programação completa do dia.
"""

from radio import executar_dia

if __name__ == "__main__":
    executar_dia()
