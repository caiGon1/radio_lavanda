# 🪻 Rádio Lavanda

> *A sua dose diária de tranquilidade, automatizada com carinho.* 🎧✨

![Python](https://img.shields.io/badge/Python-3.x-blue?style=for-the-badge&logo=python&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-Automated-2088FF?style=for-the-badge&logo=github-actions&logoColor=white)
![Status](https://img.shields.io/badge/Status-No_Ar-brightgreen?style=for-the-badge)

A **Rádio Lavanda** é um projeto automatizado criado para gerar programas de áudio, compilar blocos com música de fundo suave e publicar novos episódios sem que você precise mexer um único dedo no dia a dia. Relaxante para quem ouve, prático para quem dev.

---

## 💡 Como Funciona?

Tudo roda redondinho como uma estação de rádio de alta frequência:
[ Conteúdo / Scripts ] ➔ [ Trilha de Fundo ] ➔ [ Mixagem Automática ] ➔ [ No Ar! 🚀 ]

1. **Agendamento Robusto:** Um fluxo no GitHub Actions (`cron.yml`) acorda a aplicação nos horários programados.
2. **Processamento em Python:** O script lê as programações (arquivos JSON) e processa as locuções e áudios temporários.
3. **Harmonia Sonora:** A locução é mixada com a clássica e relaxante `musica_fundo_suave.mp3`.
4. **Entrega Pronta:** O bloco final é gerado e disponibilizado para os ouvintes!

---

## 🛠️ O que tem debaixo do capô?

* **`programas/`**: Onde ficam armazenadas as rotinas e os scripts dos programas em JSON.
* **`assets/`**: O acervo musical e sonoro (incluindo as trilhas que dão o clima suave).
* **`.github/workflows/cron.yml`**: O maestro que roda tudo automaticamente na nuvem.
* **Python**: A linguagem responsável por juntar todas as peças e fazer a magia acontecer.

---

## 🚀 Como Rodar Localmente

Quer testar a rádio na sua própria máquina? É vapt-vupt!

### 1. Clonar o repositório
```bash
git clone [https://github.com/seu-usuario/radio_lavanda.git](https://github.com/seu-usuario/radio_lavanda.git)
cd radio_lavanda
```

### 2. Configurar o ambiente
Crie seu arquivo de variáveis de ambiente com base nas suas necessidades:

```bash
cp .env.example .env  # se houver, ou crie seu arquivo .env
```

### 3. Instalar as dependências

```bash
pip install -r requirements.txt
```

### 4. Soltar o som!
Execute o script principal para gerar um bloco de áudio localmente:

```bash
python main.py  # ou o nome do seu script principal
```
O áudio gerado aparecerá temporariamente como temp_bloco_*.mp3 para você conferir a qualidade!

## 🤝 Como Contribuir
Achou o projeto legal e quer deixar a Rádio Lavanda ainda mais incrível?

1. Faça um Fork do projeto.

2. Crie uma Branch para sua funcionalidade (git checkout -b feature/nova-trilha).

3. Faça o Commit das suas alterações (git commit -m 'Adiciona nova trilha relaxante').

4. Abra um Pull Request.
