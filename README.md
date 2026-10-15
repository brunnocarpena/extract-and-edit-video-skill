# extract-and-edit-video-skill

Skill do Claude Code que garimpa depoimentos em vídeos longos do YouTube e monta o vídeo final.

0. Onboarding: pergunta o contexto do projeto e os formatos de saída e grava em `projeto.json`.
1. Puxa a playlist e separa os candidatos pelo título.
2. Baixa as legendas automáticas e converte em texto com minutagem.
3. Agentes leem cada transcrição e marcam corte longo, curto, tarja e nota A/B/C.
4. Distribui os cortes em roteiros JSON.
5. Baixa só os trechos e edita com ffmpeg: countdown, tarja, QR, fade e áudio normalizado - ou solta cortes avulsos.
6. Exporta para edição: XML para Premiere/DaVinci, pacote para CapCut e legendas SRT.

Nasceu dos intervalos do evento IDE da Mari Tortella (out/2026).

## Instalar
```bash
git clone git@github.com:brunnocarpena/extract-and-edit-video-skill.git ~/.claude/skills/extract-and-edit-video-skill
sh ~/.claude/skills/extract-and-edit-video-skill/scripts/preparar.sh
```

## Requisitos
- Python 3.11+ e ffmpeg (`brew install ffmpeg`). Não precisa de drawtext/libass.
- venv em `~/.cache/extract-and-edit-video/venv` com `yt-dlp==2026.8.19`, `pillow==12.3.0`, `segno==1.6.6` (criado pelo `preparar.sh`).
- Sem chave nem login. Vídeo privado/Hotmart é passo manual.

## Scripts
| Script | Faz |
|---|---|
| `scripts/preparar.sh` | Cria o venv e confere o ffmpeg |
| `scripts/json3_para_txt.py` | Legenda json3 → texto `[mm:ss]` em blocos de ~15 s |
| `scripts/prebaixar.py` | Baixa os cortes longos A/B dos mapas |
| `scripts/montar.py` | Monta o vídeo (ou os cortes avulsos) a partir do roteiro |
| `scripts/exportar.py` | Pacote de edição: XML (Premiere/DaVinci), clipes + tarjas (CapCut) e SRT |
| `scripts/sobreposicoes.py` | Countdown, tarja e QR em PNG, com cores/fonte do perfil |

Perfil visual de exemplo: `perfis/mari.json`. Formato do roteiro: `references/roteiro.md`. Perguntas do onboarding: `references/onboarding.md`.
