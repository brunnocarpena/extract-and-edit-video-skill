---
name: extract-and-edit-video-skill
description: Garimpa depoimentos em vídeos longos do YouTube (playlist, lives, podcasts, entrevistas) e monta o vídeo final - transcreve pelas legendas automáticas, mapeia o trecho forte de cada episódio (corte longo, corte curto, tarja, nota A/B/C), baixa só os trechos e edita com ffmpeg (countdown, tarja, QR, fade, áudio normalizado) ou solta cortes avulsos. Use quando pedirem "extrair depoimentos do YouTube", "cortar os depoimentos da playlist", "vídeo de intervalo do evento", "vídeo para o almoço/coffee break", "prova social em vídeo", "pegar os melhores trechos das lives", "achar o momento em que a aluna conta o resultado", "baixar só um trecho do vídeo", "cortes para anúncio a partir das lives", yt-dlp, download-sections, mesmo que não diga a palavra skill.
---

# Extrair e editar depoimentos do YouTube

Transforma uma playlist (ou lista de vídeos) em: **mapa** de cada episódio com o trecho que
prova a transformação → **roteiros** → **vídeo final** pronto para tocar (intervalo de evento,
abertura) ou **cortes avulsos** (anúncio, Reels, página de vendas).

Nasceu dos intervalos da IDE da Mari Tortella (out/2026): 187 episódios viraram 5 vídeos de
intervalo e 6 cortes avulsos. O exemplo completo está em `references/perfil-mari.md`.

Divisão com outras skills: esta **garimpa e corta**. Legenda palavra a palavra, vertical 9:16
com gancho, motion = `enhanced-video` em cima dos arquivos daqui. Resumo/capítulos de UM vídeo
= `youtube-content`.

## Primeira resposta: roteiro + briefing numa mensagem só

```
Vou fazer assim:
1. Preparar - pasta do projeto, venv (yt-dlp, Pillow, segno) e ffmpeg.
2. Listar - puxo a playlist e separo os candidatos pelo título.  ← você confere
3. Transcrever - legendas automáticas → texto com minutagem.
4. Mapear - agentes leem cada transcrição e marcam corte longo, curto, tarja e nota A/B/C.  ← você aprova
5. Roteiros - distribuo os cortes A/B pelos vídeos pedidos.  ← você aprova
6. Montar - baixo só os trechos e edito (countdown, tarja, QR, fade, áudio).
7. Conferir - assisto às emendas e às tarjas por amostragem e te entrego.
```

Perguntas do briefing (pule o que o pedido já respondeu; faltou resposta = siga o padrão e
liste como pendência):

| # | Pergunta | Padrão |
|---|---|---|
| 1 | Fonte: playlist, canal ou lista de links? | - (obrigatória) |
| 2 | Para que é: intervalo ao vivo, abertura, anúncio, Reels? Quantos vídeos e de que duração? | intervalo, 1 vídeo |
| 3 | Critério: o que conta como depoimento forte? Que temas ficam fora? | história do título; só A/B |
| 4 | Visual: perfil (cores, fonte, rótulo da tarja) | `perfis/mari.json` |
| 5 | Countdown ("Voltamos em") e QR (URL + legenda)? | countdown sim, QR não |
| 6 | Pasta do projeto | `<cliente>/cortes-<assunto>/` |

## Fluxo

### 1. Preparar
```bash
sh ~/.claude/skills/extract-and-edit-video-skill/scripts/preparar.sh   # venv em ~/.cache/extract-and-edit-video/venv
mkdir -p dados/mapas legendas transcricoes roteiros finais
```
`V=~/.cache/extract-and-edit-video/venv/bin` e `S=~/.claude/skills/extract-and-edit-video-skill/scripts`
nos comandos abaixo. Se o projeto já tem um venv com yt-dlp + Pillow + segno (ex.: `tools/venv`),
use `V=tools/venv/bin` em vez de criar outro. Instalar/subir versão de dependência passa antes
pelo `supply-chain-guard`.

### 2. Listar candidatos
```bash
$V/yt-dlp --flat-playlist -J "<url da playlist>" > dados/playlist.json
```
Leia os títulos e grave `dados/candidatos.txt` (um ID por linha, agrupado por tema com `#`).
Corte pelo título o que está fora do critério. **Checkpoint:** mostre a contagem por tema e os
excluídos; sem resposta, siga.

### 3. Transcrever
```bash
for id in $(grep -v '^#' dados/candidatos.txt); do
  $V/yt-dlp -q --no-warnings --skip-download --write-auto-subs --sub-langs pt --sub-format json3 \
    -o "legendas/%(id)s" "https://www.youtube.com/watch?v=$id"
  $V/python -I $S/json3_para_txt.py "legendas/$id.pt.json3" > "transcricoes/$id.txt"
done
```
Rode em background e espalhe as chamadas (pausa de 2-3 s) para não levar 429.

### 4. Mapear (agentes em paralelo)
Copie `references/mapa.md` para `dados/INSTRUCOES-MAPA.md` e preencha o Contexto com o briefing.
Despache agentes com lotes de ~8 IDs: cada um lê o arquivo de instruções e as transcrições
**inteiras** e grava `dados/mapas/<id>.json`. Sem rede para os agentes.

Depois, **revise você mesmo** antes de mostrar:
- Tarja fiel? Releia o trecho da transcrição de cada tarja com número ou palavra forte.
- Fim do corte limpo? Para cortes que terminam perto de um tema proibido, confira o tempo
  exato nas palavras do `legendas/<id>.pt.json3` (cada `seg` tem `tOffsetMs`).
- Alertas: menor de idade, nome de terceiro, promessa médica → sinalize; menor só entra com
  autorização.

Monte `dados/inventario.json` (A e B, tema, duração do longo) e **mostre a tabela A/B para
aprovação**.

### 5. Roteiros
Formato e receitas em `references/roteiro.md`. Antes, leia os `roteiros/*.json` que já existem
e anote os IDs usados. Distribua por tema para não repetir assunto em
sequência e para não repetir o mesmo episódio em vídeos que a mesma plateia vê. Some as
durações até bater o tempo pedido. **Checkpoint:** mostre cada roteiro (ordem, tarja, minutos).

### 6. Montar
```bash
$V/python -I $S/prebaixar.py           # opcional: baixa todos os longos A/B antes
$V/python -I $S/montar.py roteiros/<nome>.json
```
Rode em background (um intervalo de 70 min leva ~10-20 min no Mac). É retomável.

### 7. Conferir e entregar
- `ffprobe` na duração final; extraia 3-4 frames (`ffmpeg -ss <t> -frames:v 1`) em emendas e
  tarjas para checar sobreposição e texto.
- Entregue com `open -R <arquivo>` e o caminho absoluto em texto.
- Feche com a lista de pendências pronta para WhatsApp (bloco de código), revisando antes o que
  já foi resolvido.

## Armadilhas que já custaram tempo
- **URL sem aspas no zsh** quebra no `?v=` (glob). Sempre `"https://..."`.
- **Legenda `pt-PT` dá 429**; `--sub-langs pt` (automática) funciona.
- **yt-dlp falha à toa** às vezes: o `montar.py` já tenta 3 vezes com 10 s de pausa.
- **ffmpeg sem drawtext/libass** nesta máquina: por isso as sobreposições são PNG (Pillow).
- **libx264 lento**: o `montar.py` usa `h264_videotoolbox` quando existe.
- **Mapa pode ser lista** (2 cortes no mesmo episódio): quem lê mapa trata os dois formatos.
- **Tarja errada** passa fácil: "Materializou 630 mil" era o preço do apartamento.
- **Fim do corte** vazando para tema proibido: o da tireoide teve de acabar em 40:10, antes de
  "foi a bruxa" - só se acha olhando os tempos por palavra do json3.
- **Nome do convidado** nem sempre é o do título do episódio.
- **Menor de idade** no trecho precisa de autorização antes de usar.
- **Cache de montagem**: mudou tarja/perfil/QR, apague `montagem/<nome>/`, senão reaproveita a
  parte antiga.
- **Vídeo privado/Hotmart** não baixa sem login: passo manual pelo Brave (perfil `Default`),
  nunca matando o navegador do usuário.

## Arquivos desta skill
| Arquivo | Quando ler/usar |
|---|---|
| `scripts/preparar.sh` | Passo 1, uma vez por máquina |
| `scripts/json3_para_txt.py` | Passo 3: json3 → texto `[mm:ss]` em blocos de ~15 s |
| `references/mapa.md` | Passo 4: modelo das instruções para os agentes |
| `scripts/prebaixar.py` | Passo 6, opcional: baixa os longos A/B dos mapas |
| `scripts/montar.py` | Passo 6: monta o vídeo (ou os cortes avulsos) a partir do roteiro |
| `scripts/sobreposicoes.py` | Chamado pelo `montar.py` (countdown, tarja, QR em PNG) |
| `references/roteiro.md` | Passo 5: formato do roteiro e receitas |
| `perfis/mari.json` | Perfil visual padrão; copie e ajuste para outro cliente |
| `references/perfil-mari.md` | Exemplo real: critérios, visual e números da IDE |
