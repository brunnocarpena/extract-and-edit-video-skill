# extract-and-edit-video-skill

Skill de agente de código que garimpa depoimentos em vídeos longos do YouTube e monta o vídeo final.
Feita para **Claude Code, Codex (OpenAI) e Gemini CLI**, em **macOS, Windows e Linux**: é um
`SKILL.md` no formato aberto de Agent Skills mais scripts em Python puro.

0. Onboarding: pergunta o contexto do projeto e os formatos de saída e grava em `projeto.json`.
1. Puxa a playlist e separa os candidatos pelo título.
2. Baixa as legendas automáticas e converte em texto com minutagem.
3. O agente lê cada transcrição e marca corte longo, curto, tarja e nota A/B/C.
4. Distribui os cortes em roteiros JSON.
5. Baixa só os trechos e edita com ffmpeg: countdown, tarja, QR, fade e áudio normalizado - ou solta cortes avulsos.
6. Exporta para edição: XML para Premiere/DaVinci, pacote para CapCut e legendas SRT.

Nasceu dos intervalos do evento IDE da Mari Tortella (out/2026).

## Instalar

O repositório é privado: antes, peça acesso e faça login no GitHub no terminal
(`gh auth login`, ou o Git pede usuário e token na primeira vez).

### 1. Programas (uma vez por computador)

| Sistema | Python 3.11+ | ffmpeg | Git |
|---|---|---|---|
| macOS | `brew install python` | `brew install ffmpeg` | já vem (ou `xcode-select --install`) |
| Windows | `winget install Python.Python.3.12` | `winget install Gyan.FFmpeg` | `winget install Git.Git` |
| Linux (Ubuntu/Debian) | `sudo apt install python3 python3-venv` | `sudo apt install ffmpeg` | `sudo apt install git` |

No Windows, feche e abra o terminal depois de instalar, para o PATH atualizar.

### 2. A skill, na pasta do seu agente

| Agente | Comando |
|---|---|
| Claude Code | `git clone https://github.com/brunnocarpena/extract-and-edit-video-skill.git ~/.claude/skills/extract-and-edit-video-skill` |
| Codex | `git clone https://github.com/brunnocarpena/extract-and-edit-video-skill.git ~/.codex/skills/extract-and-edit-video-skill` |
| Gemini CLI | `gemini skills install https://github.com/brunnocarpena/extract-and-edit-video-skill.git` |

No Windows (PowerShell), se o `~` não funcionar, troque por `$HOME`
(ex.: `$HOME\.claude\skills\extract-and-edit-video-skill`). Usa mais de um agente? Clone uma vez e
aponte os outros para a mesma pasta (no Gemini: `gemini skills link <pasta>`).

### 3. Preparar (uma vez por computador)

```
macOS/Linux:  python3 ~/.claude/skills/extract-and-edit-video-skill/scripts/preparar.py
Windows:      py $HOME\.claude\skills\extract-and-edit-video-skill\scripts\preparar.py
```
Troque `.claude` pela pasta do seu agente. O script cria o venv em
`~/.cache/extract-and-edit-video/venv` com `yt-dlp==2026.8.19`, `pillow==12.3.0` e `segno==1.6.6`,
confere o ffmpeg e imprime o caminho do python que roda os outros scripts.

### 4. Usar

Reinicie o agente, abra-o **dentro da pasta do projeto** e peça em português, por exemplo:
"quero os melhores depoimentos desta playlist para o intervalo do evento". No Claude Code também
dá para chamar direto com `/extract-and-edit-video-skill`. A skill começa pelo onboarding.

Sem chave nem login. Vídeo privado/Hotmart é passo manual.

## Scripts
| Script | Faz |
|---|---|
| `scripts/preparar.py` | Cria o venv e confere o ffmpeg (macOS, Windows, Linux) |
| `scripts/transcrever.py` | Baixa as legendas dos candidatos e grava as transcrições com minutagem |
| `scripts/json3_para_txt.py` | Legenda json3 → texto `[mm:ss]` em blocos de ~15 s |
| `scripts/prebaixar.py` | Baixa os cortes longos A/B dos mapas |
| `scripts/montar.py` | Monta o vídeo (ou os cortes avulsos) a partir do roteiro |
| `scripts/exportar.py` | Pacote de edição: XML (Premiere/DaVinci), clipes + tarjas (CapCut) e SRT |
| `scripts/sobreposicoes.py` | Countdown, tarja e QR em PNG, com cores/fonte do perfil |

Perfil visual de exemplo: `perfis/mari.json` (fonte Futura, do Mac; em outro sistema entra a Jost
de `assets/fontes/`, licença OFL). Formato do roteiro: `references/roteiro.md`. Perguntas do
onboarding: `references/onboarding.md`.

Testado de ponta a ponta no macOS com Claude Code. Windows, Linux, Codex e Gemini usam os mesmos
scripts, mas ainda não rodaram um projeto real: quem for o primeiro, avise o que precisou ajustar.
