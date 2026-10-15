# Formato do roteiro (`roteiros/<nome>.json`)

```json
{
  "saida": "finais/almoco-dia1.mp4",
  "perfil": "perfil.json",
  "countdown": "Voltamos em",
  "qr": {"url": "https://...", "legenda": "Ficha de interesse"},
  "separados": false,
  "itens": [
    {"id": "AZWW4eZySeI", "ini": "25:34", "fim": "28:37",
     "tarja": "Em 7 dias, o ex ofereceu um acordo melhor",
     "rotulo": "Resultado real com a RT", "nome": "divorcio-7dias"}
  ]
}
```

| Campo | Obrigatório | O que faz |
|---|---|---|
| `saida` | sim | Arquivo final. Com `separados: true`, é uma pasta. |
| `perfil` | não | JSON de cores/fonte/rótulo (formato em `perfis/mari.json`). Sem ele, perfil da Mari. |
| `countdown` | não | Rótulo do relógio regressivo no topo, contando o total do vídeo. `null` ou ausente = sem relógio. |
| `qr` | não | QR fixo no canto inferior direito, durante o vídeo todo. |
| `separados` | não | `true` = um mp4 por item (cortes avulsos para anúncio/Reels), sem juntar. |
| `delogo` | não | Caixa `[x, y, l, a]` (em 1280x720) borrada só na versão bruta (`--cru`). Padrão: selo da live no canto superior direito (`1112, 4, 164, 152`). `false` desliga. |
| `itens[].id` | um dos dois | ID do vídeo do YouTube. |
| `itens[].arquivo` | um dos dois | Vídeo local, caminho relativo à pasta do projeto (ex.: `novos/DEP-0001.mp4`). Entra inteiro; vertical vira centralizado sobre fundo desfocado. |
| `itens[].ini`/`fim` | só com `id` | `mm:ss` ou `h:mm:ss`. |
| `itens[].delogo` | não | `false` (não borra este item) ou caixa própria `[x, y, l, a]`. Item `arquivo` nunca é borrado. |
| `itens[].tarja` | não | Frase da tarja (máx. 42 caracteres), visível do segundo 2 ao 14. |
| `itens[].rotulo` | não | Linha pequena acima da tarja. Padrão: `rotulo_tarja` do perfil. |
| `itens[].nome` | não | Usado no nome do arquivo quando `separados`. |

## Receitas
- **Intervalo de evento ao vivo** (almoço/coffee): `countdown` + `qr` + cortes longos, até
  somar a duração do intervalo (almoço ~60-75 min, coffee ~15 min com cortes curtos).
- **Abertura**: poucos cortes curtos, sem `qr`.
- **Cortes avulsos** (anúncio, Reels, página de vendas): `separados: true`, sem `countdown` e
  sem `qr`. Saem horizontais, com a duração do corte (2-3 min no curto). Versão vertical curta
  com legenda palavra a palavra é trabalho da skill `enhanced-video` em cima destes arquivos.

## Montar
De dentro da pasta do projeto (`<python>` e `<skill>` como no SKILL.md):
```
<python> -I <skill>/scripts/montar.py roteiros/<nome>.json
```
É retomável: trechos baixados ficam em `trechos/`, partes já codificadas em `montagem/<nome>/`.
Mudou tarja/QR/perfil? Apague `montagem/<nome>/` antes de rodar de novo.

## Versão bruta (sem logo e sem countdown)
```
<python> -I <skill>/scripts/montar.py roteiros/<nome>.json --cru
```
Grava `brutos/<nome>.mp4`: sem countdown, QR e tarjas, com o selo da live borrado (`delogo`).
Cache próprio em `montagem/<nome>-cru/`.

## Exportar para outro editor
```
<python> -I <skill>/scripts/exportar.py roteiros/<nome>.json premiere,capcut,srt
```
Usa o mesmo roteiro e os mesmos `trechos/` (e roda o `--cru` por baixo). Grava `editor/<nome>/`:
- `clipes/` numerados, sem logo, countdown nem tarja;
- `tarjas/` em PNG 1280x720 já na posição;
- `camadas/countdown.mov` (QuickTime Animation com transparência, vídeo inteiro),
  `camadas/countdown-chroma.mp4` (mesmo relógio sobre verde, para editor sem alfa) e `camadas/qr.png`;
- `<nome>.xml` (Premiere e DaVinci): V1 clipes, V2 tarjas, V3 countdown, V4 QR;
- `TEMPOS.csv` (onde cada clipe e tarja entra, para montar à mão no CapCut);
- SRT por clipe e da sequência, e `LEIA-ME.txt`.
