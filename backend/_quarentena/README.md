# Quarentena de testes

Estes arquivos **nao sao coletados** pelo pytest. Estao preservados, nao apagados.
O cabecalho da suite imprime o que esta aqui, para um `pytest` verde nunca
significar "tudo coberto".

Motivo comum: testam modulos que ainda sao **sincronos** e sao o proximo alvo da
frente C (async). Testes de servico sync contra `AsyncSession` nao provam nada,
entao reescrever agora seria trabalho descartado.

## `test_atendimento_service.py.legado` (317 linhas, truncado)
- Truncado no meio de `service.listar(page` -> `SyntaxError` que **interrompia a
  coleta da suíte inteira**, inclusive dos testes que passam.
- Depende de fixtures legadas (`atendimento_aberto`, `atendimento_em_fila`).
- Usa `status == "aberto"`, que nao existe em `StatusAtendimento` (valores atuais:
  aguardando, em_andamento, pausado, transferido, finalizado, cancelado).

## `test_indicadores.py.legado`
- Depende da fixture `service` para `IndicadoresService`, hoje sincrono.
- 19 referencias ao contrato legado.

## `test_atendimento_router.py.legado`
- Depende da fixture `client` (`TestClient`), que exige `app/main.py` — hoje
  inexistente. Sem entrypoint nao ha como subir a aplicacao.

**Para reativar:** reescrever do zero contra o contrato canonico, com
`AsyncSession`, apos converter cada modulo correspondente.
