# Onboarding do projeto

Mande as perguntas **numa mensagem só**, já com o padrão de cada uma. Pule o que o pedido ou a
conversa já responderam. O que ficar sem resposta segue o padrão e entra na lista de pendências,
sem travar o fluxo.

## Pergunta antes: já existe `projeto.json`?
Se a pasta do projeto já tem `projeto.json`, **não refaça o onboarding**: mostre o resumo em 5
linhas e pergunte só "mudou alguma coisa?". Sem resposta, siga com o que está salvo.

## Mensagem modelo

```
Antes de começar, preciso do contexto. Responda só o que quiser mudar; o resto vai no padrão.

Projeto
1. Cliente/marca e evento (nome e data): ex. "Mari Tortella - IDE 17-18/10"
2. O que está sendo vendido ou anunciado, e para quem
3. Fonte: playlist, canal ou lista de links (obrigatória)
4. O que conta como depoimento forte? Que temas ficam fora? (padrão: história do título; só A/B)
5. Pasta do projeto (padrão: <cliente>/cortes-<assunto>/)

Uso
6. Para que é: intervalo ao vivo, abertura, anúncio, Reels, página de vendas? (padrão: intervalo)
7. Quantos vídeos e de que duração? (padrão: 1 vídeo do tamanho do intervalo)

Formatos de saída (pode marcar vários)
8. a) MP4 final pronto para tocar, 1280x720, com tarja/countdown/QR   ← padrão
   b) Cortes avulsos em MP4, um por depoimento
   c) Projeto para Premiere Pro ou DaVinci Resolve (XML com a timeline montada)
   d) Pacote para CapCut, Final Cut ou outro editor (clipes numerados + tarjas PNG + legendas)
   e) Legendas SRT
   f) Vertical 9:16 para Reels/Stories (feito depois pela skill enhanced-video)

Visual
9. Perfil: cores, fonte e rótulo da tarja (padrão: perfis/mari.json)
10. Countdown "Voltamos em" no topo? (padrão: sim no intervalo, não no resto)
11. QR code: URL e legenda (padrão: sem QR)
```

## O que cada formato vira

| Resposta | Comando | Saída |
|---|---|---|
| a) MP4 final | `montar.py roteiros/<nome>.json` | `finais/<nome>.mp4` |
| b) Cortes avulsos | `montar.py` com `"separados": true` no roteiro | `finais/<nome>/NN_<slug>.mp4` |
| c) Premiere/DaVinci | `exportar.py roteiros/<nome>.json premiere,srt` | `editor/<nome>/<nome>.xml` + clipes + tarjas |
| d) CapCut/Final Cut/outro | `exportar.py roteiros/<nome>.json capcut` | `editor/<nome>/` clipes numerados + tarjas + SRT + LEIA-ME |
| e) SRT | `exportar.py roteiros/<nome>.json srt` | `editor/<nome>/<nome>.srt` e um por clipe |
| f) Vertical | skill `enhanced-video` em cima de b) | fora desta skill |

Formatos se combinam: "MP4 para tocar no evento e Premiere para o editor ajustar" = rodar os
dois comandos sobre o mesmo roteiro. Os trechos baixados em `trechos/` servem aos dois.

Por que o CapCut não recebe projeto pronto: ele não importa XML nem projeto de outro programa
de forma confiável. O pacote em pasta, com os arquivos numerados na ordem, é o que funciona.

## `projeto.json` (gravar na pasta do projeto ao fim do onboarding)

```json
{
  "cliente": "Mari Tortella",
  "evento": "IDE 17-18/10/2026",
  "oferta": "COMU RT - assinatura",
  "publico": "alunas e interessadas em radiestesia",
  "fonte": ["https://www.youtube.com/playlist?list=..."],
  "criterio": "resultado concreto contado pela aluna",
  "temas_fora": ["cura de doença", "religião"],
  "usos": [{"tipo": "intervalo", "quantidade": 5, "minutos": 70}],
  "formatos": ["mp4", "premiere", "srt"],
  "perfil": "perfis/mari.json",
  "countdown": "Voltamos em",
  "qr": null,
  "pendencias": ["QR: URL da ficha ainda não definida"]
}
```

O `criterio` e os `temas_fora` vão para o Contexto do `dados/INSTRUCOES-MAPA.md` (passo 4). Os
`formatos` definem os comandos do passo 6. As `pendencias` entram na lista final para o WhatsApp.
