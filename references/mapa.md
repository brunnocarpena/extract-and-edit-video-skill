# Instruções de mapeamento (modelo para os agentes)

Copie este arquivo para `dados/INSTRUCOES-MAPA.md` do projeto e preencha o bloco **Contexto**
com o briefing do pedido (marca, evento, critérios, o que fica fora). Cada agente recebe um lote
de IDs e lê este arquivo antes de começar.

---

## Contexto (preencher)
- Marca / cliente: ...
- Para que servem os cortes: (intervalo de evento ao vivo, anúncio, Reels, página de vendas...)
- Oferta ou mensagem que os depoimentos sustentam: ...
- Critério de escolha: o corte é o momento em que o convidado conta a história que está no
  **título** do episódio. O título é o filtro.
- Fica fora: (temas que a marca não quer associar ao produto)
- Só as transformações mais **fortes** entram; episódio fraco recebe nota C.

## Tarefa
Para cada ID do seu lote, leia a transcrição **inteira** (`transcricoes/<id>.txt`, blocos de
~15 s com `[mm:ss]` ou `[h:mm:ss]`) e grave `dados/mapas/<id>.json`:

```json
{
  "id": "<id>",
  "titulo": "<título do episódio>",
  "convidado": "<primeiro nome, se for dito; senão null>",
  "tema": "<um dos temas do briefing>",
  "forca": "A | B | C",
  "motivo_forca": "<1 frase: resultado concreto? número, prazo, antes/depois claro?>",
  "longo": {"ini": "mm:ss", "fim": "mm:ss"},
  "curto": {"ini": "mm:ss", "fim": "mm:ss"},
  "tarja": "<frase curta, máx 42 caracteres, com acentos>",
  "resumo": "<2 frases do que a pessoa conta no trecho>",
  "alertas": "<tema proibido, promessa médica absoluta, nome de terceiro, menor de idade, palavrão, áudio ruim; ou null>"
}
```

Se o episódio tiver 2 histórias fortes e distintas, grave uma **lista** com os 2 objetos no
mesmo arquivo.

## Regras de corte
- **longo**: 4 a 8 min. Começa quando o convidado começa a contar a história do título
  (incluindo o "antes"), termina logo depois do resultado, antes de o apresentador mudar de
  assunto ou ir para pitch/aviso.
- **curto**: 1:30 a 3:00, dentro do longo: problema → o que fez → resultado. Precisa fazer
  sentido sozinho.
- Não começar no meio de uma frase do apresentador; preferir o bloco anterior.
- Evitar trechos com horário de live, cupom, link, "evento daqui a X dias" - envelhecem o corte.
- Se a história do título não aparecer com clareza: `forca = "C"` e explique.
- **Tarja fiel ao que a pessoa disse.** Nada de "curou" se ela não afirmou; conferir de quem é
  cada número (ex.: "630 mil" era o preço do apartamento, não o valor materializado).
- Nome do convidado pode não bater com o título do episódio: use o que ele diz na conversa.

## Limites
Não baixar nada, não rodar comando de rede. Só ler os `.txt` e escrever os `.json`.
