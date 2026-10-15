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
| `itens[].id` | sim | ID do vídeo do YouTube. |
| `itens[].ini`/`fim` | sim | `mm:ss` ou `h:mm:ss`. |
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
```bash
cd <pasta do projeto>
~/.cache/extract-and-edit-video/venv/bin/python -I ~/.claude/skills/extract-and-edit-video-skill/scripts/montar.py roteiros/<nome>.json
```
É retomável: trechos baixados ficam em `trechos/`, partes já codificadas em `montagem/<nome>/`.
Mudou tarja/QR/perfil? Apague `montagem/<nome>/` antes de rodar de novo.
