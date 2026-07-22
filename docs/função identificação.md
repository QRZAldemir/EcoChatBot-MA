# Função de Identificação de Contatos — Retorno Pendente e Atendimento em Andamento

> Status: **análise / backlog** — funcionalidade observada no ZigChat, ainda em fase de teste comparativo. Este documento é o *prompt* de especificação a ser usado futuramente para implementar a função no EcoChatBot-MA. Não afeta o fluxo atual de XLSX → dashboard (`modulo_dashboard.html`).

## 1. Contexto

Durante a análise do ZigChat como referência de mercado, foi identificada uma funcionalidade que ainda não existe no EcoChatBot-MA: o sistema reconhece automaticamente quando um contato que está entrando em conversa **já tentou ser atendido antes sem sucesso**, ou **já está sendo atendido no momento** por outro colaborador/fila.

## 2. Problema a resolver

1. Um cliente entra em contato, mas o atendimento não é concluído (ex.: cliente some, atendente não consegue resolver na hora).
2. O atendente pergunta: *"Você deseja que entremos em contato em outro dia?"*
3. Se o cliente aceitar, esse contato deveria ficar **marcado para retorno**.
4. Quando esse mesmo contato voltar a escrever (em outro dia), o sistema hoje **não identifica** que se trata de um retorno pendente — o atendente não tem visibilidade disso.
5. Além disso, se um cliente que **já está em atendimento ativo** (com outro atendente) tentar abrir conversa novamente, o sistema também não avisa isso, podendo gerar atendimento duplicado/concorrente.

## 3. Objetivo da função

Criar uma função — sugestão de nome `identificarStatusContato(contatoId)` — que, a cada novo contato recebido (ou reaberto), consulte o histórico e classifique o contato em um destes status:

| Status | Significado |
|---|---|
| `NOVO` | Primeiro contato, sem histórico de atendimento. |
| `RETORNO_PENDENTE` | Atendimento anterior não teve sucesso **e** o cliente aceitou ser recontatado em outro dia. |
| `EM_ATENDIMENTO` | O contato já possui um atendimento em aberto, com outro atendente, neste exato momento. |
| `FINALIZADO` | Último atendimento foi concluído com sucesso — sem pendência. |

## 4. Regras de negócio

- Um atendimento é considerado **"sem sucesso"** quando é encerrado sem resolução e o atendente registra a resposta do cliente à pergunta de reagendamento.
- O campo `deseja_retorno` só é `true` se o cliente responder afirmativamente à pergunta *"Você deseja que entremos em contato em outro dia?"*.
- O status `RETORNO_PENDENTE` só é válido a partir do **dia seguinte** ao atendimento sem sucesso (evita confundir com o mesmo dia).
- O status `EM_ATENDIMENTO` tem prioridade sobre `RETORNO_PENDENTE` — se o contato está sendo atendido agora, isso deve aparecer primeiro.
- Um contato só pode ter **um atendimento em aberto por vez** (regra de exclusividade), servindo de base para o alerta de duplicidade.

## 5. Fluxo proposto

1. Mensagem recebida → sistema busca o contato pelo identificador único (telefone/WhatsApp ID).
2. Verifica se existe atendimento com `status = em_atendimento` para esse contato:
   - Se sim → retorna `EM_ATENDIMENTO`, identifica o atendente responsável e **alerta** o operador atual (impede ou avisa antes de abrir novo atendimento).
3. Caso não esteja em atendimento, verifica o último atendimento encerrado:
   - Se `status = sem_sucesso` e `deseja_retorno = true` e `data_atendimento < hoje` → retorna `RETORNO_PENDENTE`.
4. Contatos com `RETORNO_PENDENTE` alimentam uma **lista/painel de retornos pendentes**, visível ao atendente/operador, com ordenação por data (mais antigos primeiro).
5. Ao abrir o atendimento a partir dessa lista, o sistema marca o retorno como tratado (`deseja_retorno = false` ou novo registro de atendimento).

## 6. Dados / modelo necessário

Extensão sugerida na tabela/coleção de atendimentos:

```
atendimentos {
  id
  contato_id
  atendente_id
  status            // em_atendimento | sem_sucesso | finalizado
  data_inicio
  data_fim
  deseja_retorno    // boolean, só relevante quando status = sem_sucesso
  data_retorno_sugerida
}
```

- Índice por `contato_id + status` para consulta rápida na entrada de cada mensagem.

## 7. Interface / UX (proposta)

- Painel **"Retornos Pendentes"** na lateral do dashboard do atendente, com filtro por data/atendente de origem.
- Badge/alerta no card do contato quando ele já estiver **em atendimento** por outro colaborador (ex.: "Em atendimento com [nome do atendente]").
- Ao abrir uma conversa de um contato marcado como retorno pendente, exibir aviso no topo: "Este contato solicitou retorno em [data]".

## 8. Critérios de aceite

- [ ] Sistema identifica corretamente contatos com atendimento anterior sem sucesso e retorno aceito, apresentando-os na lista de retornos pendentes.
- [ ] Sistema identifica e alerta quando um contato já está em atendimento simultâneo, evitando duplicidade.
- [ ] Lista de retornos pendentes é visível e filtrável pelo atendente/operador.
- [ ] Marcação de retorno pendente é limpa automaticamente após o novo atendimento ser aberto.

## 9. Referência

Comportamento observado e usado como referência: **ZigChat** (em fase de teste/análise comparativa pelo time — ainda não implementado no EcoChatBot-MA).

---

## 10. Prompt para desenvolvimento futuro

> Use o texto abaixo como prompt ao retomar esta tarefa (para si mesmo ou para uma IA de apoio ao desenvolvimento):

```
Implemente no EcoChatBot-MA uma função de identificação de status de contato,
chamada ao receber uma nova mensagem/atendimento, com as seguintes regras:

1. Se o contato já possui um atendimento em aberto (status = em_atendimento)
   com outro colaborador, retornar EM_ATENDIMENTO e alertar o operador atual
   antes de permitir abrir um novo atendimento para o mesmo contato.

2. Se o último atendimento do contato foi encerrado sem sucesso
   (status = sem_sucesso) E o cliente respondeu "sim" à pergunta
   "Você deseja que entremos em contato em outro dia?" (deseja_retorno = true)
   E a data desse atendimento é anterior ao dia atual, retornar
   RETORNO_PENDENTE.

3. Contatos com RETORNO_PENDENTE devem aparecer em uma lista/painel
   "Retornos Pendentes" visível ao atendente/operador, ordenada por data
   mais antiga primeiro.

4. Contatos em EM_ATENDIMENTO devem gerar alerta visual (badge) mostrando
   qual atendente já está responsável por aquele contato.

5. Basear-se no modelo de dados de "atendimentos" já existente no projeto,
   estendendo os campos deseja_retorno e data_retorno_sugerida quando
   necessário.

Referência de comportamento: funcionalidade equivalente observada no ZigChat.
```
