---
name: extract-and-edit-video-skill
description: Garimpa depoimentos em vídeos longos do YouTube (playlist, lives, podcasts, entrevistas) e monta o vídeo final - transcreve pelas legendas automáticas, mapeia o trecho forte de cada episódio (corte longo, corte curto, tarja, nota A/B/C), baixa só os trechos e edita com ffmpeg (countdown, tarja, QR, fade, áudio normalizado), solta cortes avulsos ou exporta para Premiere/DaVinci (XML), CapCut e SRT. Começa com um onboarding do projeto (contexto e formatos de saída). Use quando pedirem "extrair depoimentos do YouTube", "cortar os depoimentos da playlist", "vídeo de intervalo do evento", "vídeo para o almoço/coffee break", "prova social em vídeo", "pegar os melhores trechos das lives", "achar o momento em que a aluna conta o resultado", "baixar só um trecho do vídeo", "cortes para anúncio a partir das lives", "exportar para o Premiere", "projeto para o CapCut", "mandar para o editor", "legenda SRT dos cortes", yt-dlp, download-sections, mesmo que não diga a palavra skill.
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

## Primeira resposta: roteiro + onboarding numa mensagem só

```
Vou fazer assim:
1. Preparar - pasta do projeto, venv (yt-dlp, Pillow, segno) e ffmpeg.
2. Listar - puxo a playlist e separo os candidatos pelo título.  ← você confere
3. Transcrever - legendas automáticas → texto com minutagem.
4. Mapear - leio cada transcrição em lotes e marco corte longo, curto, tarja e nota A/B/C.  ← você aprova
5. Roteiros - distribuo os cortes A/B pelos vídeos pedidos.  ← você aprova
6. Montar e exportar - baixo só os trechos e gero cada formato pedido (MP4, Premiere, CapCut, SRT).
7. Conferir - assisto às emendas e às tarjas por amostragem e te entrego.
```

Logo abaixo do roteiro, as perguntas do onboarding de `references/onboarding.md`: contexto do
projeto (cliente, evento, oferta, público, fonte, critério, temas fora, pasta), uso (intervalo,
abertura, anúncio, Reels; quantos e de que duração), **formatos de saída** (MP4 final, cortes
avulsos, Premiere/DaVinci, CapCut/outro editor, SRT, vertical) e visual (perfil, countdown, QR).
Cada pergunta leva o padrão; o que ficar sem resposta segue o padrão e vira pendência.

Grave as respostas em `projeto.json` na pasta do projeto. Na próxima vez que a skill rodar ali,
mostre o resumo do `projeto.json` e pergunte só o que mudou.

## Fluxo

Vale para qualquer agente (Claude Code, Codex, Gemini CLI) e qualquer sistema (macOS, Windows,
Linux): todo passo é um script Python, sem `bash`, `for` ou `>` do shell. Nos comandos abaixo:
- `<skill>` = a pasta onde está este SKILL.md.
- `<python>` = o python do venv, impresso no fim do `preparar.py`:
  macOS/Linux `~/.cache/extract-and-edit-video/venv/bin/python`;
  Windows `%USERPROFILE%\.cache\extract-and-edit-video\venv\Scripts\python.exe`.
Rode tudo de dentro da pasta do projeto, com aspas em caminhos que tenham espaço.

### 1. Preparar
```
python3 <skill>/scripts/preparar.py      # Windows: py <skill>\scripts\preparar.py
```
Cria o venv (uma vez por máquina) e confere o ffmpeg; se faltar, mostra o comando de instalar
daquele sistema (brew, winget, apt). Crie na pasta do projeto `dados/mapas`, `roteiros` e
`finais` e grave ali o `projeto.json` do onboarding. Se o projeto já tem um venv com yt-dlp +
Pillow + segno (ex.: `tools/venv`), use o python dele. Instalar/subir versão de dependência passa
antes pela checagem de supply chain (no Claude Code desta casa: `supply-chain-guard`).

### 2. Listar candidatos
```
<python> -m yt_dlp -q --flat-playlist --skip-download --print-to-file "%(id)s	%(title)s" dados/playlist.tsv "<url da playlist>"
```
(entre `%(id)s` e `%(title)s` vai um TAB). Leia os títulos e grave `dados/candidatos.txt` (um ID
por linha, agrupado por tema com `#`). Corte pelo título o que está fora do critério.
**Checkpoint:** mostre a contagem por tema e os excluídos; sem resposta, siga.

### 3. Transcrever
```
<python> -I <skill>/scripts/transcrever.py
```
Baixa a legenda automática de cada candidato e grava `transcricoes/<id>.txt` com minutagem.
Pausa 2-3 s entre vídeos (evita 429) e é retomável. Se o seu agente roda comando em segundo
plano, rode assim; é demorado com muitos vídeos.

### 4. Mapear (em lotes)
Copie `references/mapa.md` para `dados/INSTRUCOES-MAPA.md` e preencha o Contexto com o
`projeto.json` (oferta, público, critério, temas fora).
Divida em lotes de ~8 IDs: cada lote lê o arquivo de instruções e as transcrições **inteiras** e
grava `dados/mapas/<id>.json`. Se o seu agente consegue despachar subagentes (no Claude Code,
sim), rode os lotes em paralelo, sem rede; se não, faça os lotes você mesmo, um de cada vez.

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

### 6. Montar e exportar
Rode o comando de cada formato do `projeto.json` (tabela em `references/onboarding.md`):
```
<python> -I <skill>/scripts/prebaixar.py                                   # opcional: baixa todos os longos A/B antes
<python> -I <skill>/scripts/montar.py roteiros/<nome>.json                 # MP4 final (ou avulsos, com separados)
<python> -I <skill>/scripts/exportar.py roteiros/<nome>.json premiere,srt  # Premiere/DaVinci: XML + clipes + tarjas
<python> -I <skill>/scripts/exportar.py roteiros/<nome>.json capcut        # CapCut/outro: clipes numerados + tarjas + SRT
```
Rode em segundo plano se puder (um intervalo de 70 min leva ~10-20 min num Mac com
`h264_videotoolbox`; no Windows/Linux, com libx264, conte com mais). É retomável, e os dois
scripts reaproveitam os mesmos `trechos/`. O `exportar.py` grava em `editor/<nome>/` com um
`LEIA-ME.txt` que explica como abrir em cada programa; entregue a pasta inteira (o XML aponta
para os arquivos dela pelo caminho absoluto).

### 7. Conferir e entregar
- `ffprobe` na duração final; extraia 3-4 frames (`ffmpeg -ss <t> -frames:v 1`) em emendas e
  tarjas para checar sobreposição e texto.
- Entregue abrindo a pasta para o usuário - macOS `open -R "<arquivo>"`, Windows
  `explorer /select,"<arquivo>"`, Linux `xdg-open "<pasta>"` - e com o caminho absoluto em texto.
- Feche com a lista de pendências pronta para WhatsApp (bloco de código), revisando antes o que
  já foi resolvido.

## Armadilhas que já custaram tempo
- **URL sem aspas no zsh** quebra no `?v=` (glob). Sempre `"https://..."`.
- **Legenda `pt-PT` dá 429**; `--sub-langs pt` (automática) funciona.
- **yt-dlp falha à toa** às vezes: o `montar.py` já tenta 3 vezes com 10 s de pausa.
- **ffmpeg sem drawtext/libass** nesta máquina: por isso as sobreposições são PNG (Pillow).
- **libx264 lento**: o `montar.py` usa `h264_videotoolbox` quando existe (Mac); no Windows/Linux
  cai no libx264 `veryfast`.
- **`>` do PowerShell grava em UTF-16** e estraga JSON e acentos: por isso a lista sai por
  `--print-to-file` e a transcrição pelo `transcrever.py`, que gravam UTF-8 direto.
- **Fonte do perfil só existe num sistema** (a Futura da Mari é do Mac): fora dele o
  `sobreposicoes.py` usa a Jost de `assets/fontes` e avisa. Perfil novo pode apontar para um
  `.ttf` dentro da pasta do projeto, que vale em qualquer sistema.
- **Mapa pode ser lista** (2 cortes no mesmo episódio): quem lê mapa trata os dois formatos.
- **Importação no Premiere/DaVinci/CapCut ainda não foi testada num editor de verdade** (nenhum
  instalado nesta máquina): o XML passa no parser e os tempos conferem. No primeiro uso real, peça
  para quem edita confirmar e anote aqui o que precisou ajustar.
- **XML com caminho absoluto**: mover a pasta `editor/<nome>/` para outro computador faz o
  Premiere/DaVinci pedir para religar a mídia (aponte para `clipes/` e ele acha o resto).
- **Tarja errada** passa fácil: "Materializou 630 mil" era o preço do apartamento.
- **Fim do corte** vazando para tema proibido: o da tireoide teve de acabar em 40:10, antes de
  "foi a bruxa" - só se acha olhando os tempos por palavra do json3.
- **Nome do convidado** nem sempre é o do título do episódio.
- **Menor de idade** no trecho precisa de autorização antes de usar.
- **Cache de montagem**: mudou tarja/perfil/QR, apague `montagem/<nome>/`, senão reaproveita a
  parte antiga.
- **Selo da live gravado no vídeo** (COMU | RT, StreamYard): fica no canto superior direito
  dos episódios; a versão bruta borra com `delogo`. Fonte nova com selo em outro lugar: ajuste
  `delogo` no roteiro e confira um frame do `brutos/`.
- **CapCut não importa XML**: o pacote dele é clipes + tarjas + camadas + `TEMPOS.csv`, montado à mão.
- **Countdown em ProRes 4444 passa de 10 GB** num almoço de 2 h; o `exportar.py` usa QuickTime
  Animation (qtrle), que fica em dezenas de MB.
- **openpyxl não está no venv**: planilha .xlsx simples dá para gerar com `zipfile` puro.
- **Vídeo privado/Hotmart** não baixa sem login: passo manual no navegador do usuário, nunca
  matando o navegador dele.

## Arquivos desta skill
| Arquivo | Quando ler/usar |
|---|---|
| `scripts/preparar.py` | Passo 1, uma vez por máquina (macOS, Windows, Linux) |
| `scripts/transcrever.py` | Passo 3: legendas de `dados/candidatos.txt` → `transcricoes/` |
| `scripts/json3_para_txt.py` | Chamado pelo `transcrever.py`: json3 → texto `[mm:ss]` em blocos de ~15 s |
| `references/mapa.md` | Passo 4: modelo das instruções para os agentes |
| `scripts/prebaixar.py` | Passo 6, opcional: baixa os longos A/B dos mapas |
| `scripts/montar.py` | Passo 6: monta o vídeo (ou os cortes avulsos) a partir do roteiro |
| `references/onboarding.md` | Primeira resposta: perguntas, formatos de saída e `projeto.json` |
| `scripts/exportar.py` | Passo 6: pacote para Premiere/DaVinci (XML), CapCut/outro editor e SRT |
| `scripts/sobreposicoes.py` | Chamado pelo `montar.py` e pelo `exportar.py` (countdown, tarja, QR em PNG) |
| `references/roteiro.md` | Passo 5: formato do roteiro e receitas |
| `perfis/mari.json` | Perfil visual padrão; copie e ajuste para outro cliente |
| `assets/fontes/` | Jost (OFL), fonte reserva quando a do perfil não existe na máquina |
| `references/perfil-mari.md` | Exemplo real: critérios, visual e números da IDE |
