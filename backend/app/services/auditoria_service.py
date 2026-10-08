"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-MA · auditoria_service
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     auditoria_service.py
@module   Backend / App / Services / auditoria_service
@author   Aldemir Queiroz
@since    2026
@version  1.0.0
───────────────────────────────────────────────────────────────────────────

FUNCIONALIDADE
──────────────
Auditoria de recuperação: responde "onde a empresa PERDEU cliente?".

O sistema classifica TODO atendimento em uma de cinco situações, e o
gestor ataca os grupos que precisam de ação humana. É um relatório
de perda, não de atendimento.

    🔴 CRÍTICO                    o cliente someu sem nem ser roteado
    🟣 DIRECIONADO SEM ATENDIMENTO  foi para um departamento, ninguém pegou
    🤖 ROBÔ FECHOU                o bot encerrou sozinho
    🟡 AGUARDANDO RESPOSTA        tem atendente, cliente esperando
    ✅ OK                         alguém atendeu

O campo mais valioso é o 🔴. Um cliente que entra, cai no menu e
desaparece sem nem aparecer para um departamento é falha da EMPRESA, não
do cliente — e é invisível em qualquer relatório de volume.

AS REGRAS, E DE ONDE VIEM
─────────────────────────
Não foram inventadas aqui. A lógica é a mesma do painel de auditoria que
o frontend já executa em JavaScript (`modulo_dashboard.html`,
função `classificarRegistro`), que é o comportamento que o gestor passou
anos olhando. Traduzir para Python sem mudá-la é o ponto: um número de
auditoria que diverge entre o PDF e a tela é pior do que não ter.

RELACIONAMENTO
──────────────
    ┌──────────────────────────────────────────────────────────────────┐
    │ RelatorioService.exportar_html_auditoria                        │
    │   ├─► classificar_pendencia(at)   1 por atendimento              │
    │   └─► gerar_indicadores(todos)    1 por relatório               │
    │         └─► _TEMPLATE_AUDITORIA  (os 4 grupos + taxa)           │
    └──────────────────────────────────────────────────────────────────┘
                          ▲
                          │ TYPE_CHECKING (nunca em runtime)
    ┌─────────────────────┴────────────────────────────────────────────┐
    │ AtendimentoRelatorioDTO  (definido em relatorio_service)         │
    │   finalizado_sem_atendimento · aguardando_atendimento            │
    │   atendente_usuario · criacao · finalizacao                      │
    └──────────────────────────────────────────────────────────────────┘

    IMPORT CIRCULAR — POR QUE O DTO SÓ APARECE EM TYPE_CHECKING
    ──────────────────────────────────────────────────────────────
    `relatorio_service` IMPORTA este módulo. Se aqui houvesse
    `from app.services.relatorio_service import AtendimentoRelatorioDTO` no
    topo, os dois se importariam em loop e o segundo a carregar encontraria
    o outro pela metade — o erro seria `cannot import name ... from
    partially initialized module`, que não mencionacircular nem aponta o
    arquivo. Com `TYPE_CHECKING`, a anotação existe para o editor e o
    import real nunca acontece.

REGRAS DE NEGÓCIO
─────────────────
    · `finalizado_sem_atendimento` e `aguardando_atendimento` chegam
      JÁ calculados do banco. Este módulo não recalcula tempo nem status:
      quem calcula é `RelatorioService`, e duplicar a conta faria os dois
      divergirem na primeira mudança de regra.
    · As funções públicas são de módulo, e não métodos, porque
      `relatorio_service` as importa diretamente. A regra está na classe
      `AuditoriaRecuperacao`; as funções são a porta de entrada fina.
    · `ClassificacaoPendencia` é `Literal` de texto, e não `Enum`, porque o
      chamador usa o retorno como CHAVE de dicionário já inicializado com
      strings. Um Enum exigiria `grupos[ClassificacaoPendencia.CRITICO]`
      e quebraria o contrato existente.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from __future__ import annotations

import math
from datetime import datetime
from typing import TYPE_CHECKING, Dict, List, Sequence, Tuple

if TYPE_CHECKING:
    from app.services.relatorio_service import AtendimentoRelatorioDTO


# ─────────────────────────────────────────────────────────────────────────────
# BLOCO 0 — O CONTRATO
# ─────────────────────────────────────────────────────────────────────────────

#: As cinco situações possíveis de um atendimento na auditoria.
#:
#: `Literal` e não `Enum` porque o retorno é usado como chave de dicionário
#: já montado com strings:
#:
#:     grupos = {"critico": [], "direcionado": [], "robo": [],
#:               "aguardando": [], "ok": []}
#:     grupos[classificar_pendencia(at)].append(at)
#:
#: Com Enum, essa linha passaria a exigir `Enum(...)` e o contrato mudaria.
#: Os nomes são os mesmos do relatório HTML (`_TEMPLATE_AUDITORIA`), e foi
#: por isso que ficaram minúsculos: são as chaves dos grupos lá também.
ClassificacaoPendencia = str

#: Faixas de simulação da taxa de sucesso.
#:
#: Recuperar uma parte dos atendimentos com problema é a pergunta que o
#: gestor faz depois de ler o relatório. Simular 25%, 50% e 75% responde
#: "vale a pena contratar mais um atendente?" sem precisar场内 disso.
PERCENTUAIS_CENARIO: Tuple[float, ...] = (0.25, 0.50, 0.75)


class AuditoriaRecuperacao:
    """
    Regras da auditoria de recuperação.

    ─────────────────────────────────────────────────────────────────────
    POR QUE CLASSE COM ESTÁTICOS, E NÃO SÓ FUNÇÕES
    ─────────────────────────────────────────────────────────────────────
    Duas razões, ambas sobre manutenibilidade:

    1) As constantes (faixas de criticidade, percentuais) ficam perto da
       lógica que as usa. Espalhadas em `constantes.py` num projeto
       pequeno, desistem de ser lidas junto do `if` que as consulta.
    2) É possível instanciar com um "agora" fixo e escrever teste de
       tempo sem `freezegun`.

    Não há estado a guardar — daí os `@staticmethod`. Se amanhã houver
    cache de classificação por período, os métodos viram de instância
    sem quebrar quem já chama.
    """

    # ─────────────────────────────────────────────────────────────────────
    # O EIXO DA CLASSIFICAÇÃO
    # ─────────────────────────────────────────────────────────────────────

    #: Marcadores do "finalizado sem atendimento", na notação do painel.
    FINALIZADO_SEM_ATENDIMENTO_SIM = "S"
    FINALIZADO_SEM_ATENDIMENTO_NAO = "N"
    FINALIZADO_SEM_ATENDIMENTO_BRANCO = ""

    @staticmethod
    def _marcador_finalizacao(atendimento: "AtendimentoRelatorioDTO") -> str:
        """
        Traduz o atendimento para o marcador de três estados.

        ─────────────────────────────────────────────────────────────────────
        POR QUE TRÊS ESTADOS, E NÃO UM BOOLEAN
        ─────────────────────────────────────────────────────────────────────
        O painel original lê uma planilha onde "Finalizado sem Atendimento"
        vinha em três valores: `S`, `N` e BRANCO. O branco não é ruído —
        significa "não há atendente E falta uma das datas", que é uma
        situação diferente de "tem atendente".

        Aqui o DTO traz `finalizado_sem_atendimento: bool`, que sozinho
        não distingue as duas últimas situações. O branco é reconstruído
        a partir de `atendente_usuario`: sem atendente, o registro nunca
        foi "finalizado sem atendimento" — o robô não o fechou.

        ─────────────────────────────────────────────────────────────────────
        POR QUE OLHAR `atendente_usuario` E NÃO `finalizacao`
        ─────────────────────────────────────────────────────────────────────
        Porque "sem atendente" é exatamente o que a coluna diz, e é o que
        o gestor reconhece. Inferir por `finalizacao is None` daria
        resultado diferente para um registro sem atendente e sem data de
        finalização — que é justamente o caso crítico.

        ─────────────────────────────────────────────────────────────────────
        POR QUE `.strip()` NO NOME DO ATENDENTE
        ─────────────────────────────────────────────────────────────────────
        O painel original faz `String(r[atendCol]||'').trim()`, e um
        nome com espaço em volta é tão vazio quanto uma string vazia. Em
        Python, `"   "` é verdadeiro — sem o `strip`, um atendente
        apagado sem limpar o campo seria lido como "TEM atendente", e o
        registro sairia de 🔴 crítico para ✅ ok. O pior desvio possível
        num relatório de perda: some um cliente da lista de problema.
        """
        if atendimento.finalizado_sem_atendimento:
            return AuditoriaRecuperacao.FINALIZADO_SEM_ATENDIMENTO_SIM

        # `strip()` antes de testar: nome só com espaço não é atendente.
        if (atendimento.atendente_usuario or "").strip():
            return AuditoriaRecuperacao.FINALIZADO_SEM_ATENDIMENTO_NAO

        return AuditoriaRecuperacao.FINALIZADO_SEM_ATENDIMENTO_BRANCO

    @staticmethod
    def classificar(atendimento: "AtendimentoRelatorioDTO") -> ClassificacaoPendencia:
        """
        Classifica UM atendimento.

        ─────────────────────────────────────────────────────────────────────
        A TABELA DE DECISÃO
        ─────────────────────────────────────────────────────────────────────
            Marcador │ Aguardando │ Resultado      │ Por quê
            ─────────┼────────────┼────────────────┼───────────────────
            S        │ S ou N     │ robo           │ o robô fechou sozinho
            N        │ S          │ aguardando     │ tem atendente, cliente espera
            N        │ N          │ ok             │ alguém atendeu
            branco   │ S          │ direcionado    │ roteado, ninguém pegou
            branco   │ N          │ critico        │ sumiu sem ser roteado

        ─────────────────────────────────────────────────────────────────────
        POR QUE O MARCADOR É CONSULTADO PRIMEIRO
        ─────────────────────────────────────────────────────────────────────
        Porque ele sozinho já resolve três das cinco linhas, e é o dado
        mais confiável dos dois: vem de `finalizado_sem_atendimento`, que
        tem regra explícita na origem. `aguardando_atendimento` é
        derivado de tempo de espera e é o que dá granularidade.

        ─────────────────────────────────────────────────────────────────────
        POR QUE `S` + `aguardando` VAI PARA `robo`
        ─────────────────────────────────────────────────────────────────────
        Essa combinação é contraditória: não há ninguém esperando e,
        ao mesmo tempo, o cliente está marcado como aguardando. O painel
        original a jogava em "nao classificados", um sixth grupo que
        existe no JavaScript mas não no contrato Python.

        Aqui ela vai para `robo`, e a justificativa é a semântica do
        próprio marcador: "finalizado sem atendimento" significa, por
        definição, que o robô encerrou. Esconder em `ok` seria pior —
        um robô fechando conversa é problema, não sucesso. A diferença
        em relação ao painel é deliberada e está registrada aqui para
        ninguém descobrir comparando os dois números depois.
        """
        marcador = AuditoriaRecuperacao._marcador_finalizacao(atendimento)
        aguardando = bool(atendimento.aguardando_atendimento)

        if marcador == AuditoriaRecuperacao.FINALIZADO_SEM_ATENDIMENTO_SIM:
            return "robo"

        if marcador == AuditoriaRecuperacao.FINALIZADO_SEM_ATENDIMENTO_NAO:
            return "aguardando" if aguardando else "ok"

        # Marcador em branco: sem atendente. Tudo aqui é pendência.
        return "direcionado" if aguardando else "critico"

    # ─────────────────────────────────────────────────────────────────────
    # OS INDICADORES
    # ─────────────────────────────────────────────────────────────────────

    @staticmethod
    def contar(
        atendimentos: Sequence["AtendimentoRelatorioDTO"],
    ) -> Dict[str, int]:
        """
        Conta quantos atendimentos caem em cada situação.

        Devolve um dicionário com as CINCO chaves, sempre. Mesmo com
        lista vazia, todas existem com zero. A razão é o relatório: o
        template faz `len(grupos["robo"])` direto, e um `KeyError` em
        relatório de empresa sem pendências é o pior lugar para um erro.
        """
        contagem: Dict[str, int] = {
            "critico": 0,
            "direcionado": 0,
            "robo": 0,
            "aguardando": 0,
            "ok": 0,
        }
        for atendimento in atendimentos:
            contagem[AuditoriaRecuperacao.classificar(atendimento)] += 1
        return contagem

    @staticmethod
    def taxa_sucesso(atendimentos: Sequence["AtendimentoRelatorioDTO"]) -> float:
        """
        Percentual de atendimentos que alguém atendeu de fato.

        ─────────────────────────────────────────────────────────────────────
        POR QUE DIVIDIR POR TODOS, E NÃO SÓ PELOS FINALIZADOS
        ─────────────────────────────────────────────────────────────────────
        "Taxa de sucesso" que ignora os pendentes mente a favor: se 90
        foram atendidos e 10 evaporaram, o número é 90% e a empresa não
        tem do que se Varso. Denominador é o total, sempre.

        Lista vazia devolve 0.0, e não erro: relatório de período sem
        movimento é resultado válido, não falha.
        """
        total = len(atendimentos)
        if total == 0:
            return 0.0

        contagem = AuditoriaRecuperacao.contar(atendimentos)
        # "ok" é o único grupo que NÃO é pendência. "robo" conta como
        # problema: o cliente não foi atendido por uma pessoa.
        problemas = total - contagem["ok"]
        return round(((total - problemas) / total) * 100, 1)

    @staticmethod
    def cenarios(
        atendimentos: Sequence["AtendimentoRelatorioDTO"],
        *,
        percentuais: Sequence[float] = PERCENTUAIS_CENARIO,
    ) -> List[Dict[str, float | int]]:
        """
        Simula o ganho de recuperar parte das pendências.

        ─────────────────────────────────────────────────────────────────────
        O QUE ESTA TABELA RESPONDE
        ─────────────────────────────────────────────────────────────────────
        "Se eu recuperar metade do que está travado, minha taxa sobe para
        quanto?" — é a pergunta que decide orçamento de atendente. Ela não
        tem resposta no relatório estático; tem aqui.

        `delta_pp` é a variação EM PONTO PERCENTUAL, não em relativo.
        Sete pontos percentuais e "sobe 7%" não são a mesma frase, e a
        leitura errada muda a decisão.

        ─────────────────────────────────────────────────────────────────────
        POR QUE O CENÁRIO 100% NÃO ENTRA
        ─────────────────────────────────────────────────────────────────────
        Porque 100% de recuperação em atendimento humano não é um cenário,
        é ficção. Recuperar a totalidade implicaria responder todo mundo
        instantaneamente — o relatório pararia de ser uma meta e viraria
        ficção.

        ─────────────────────────────────────────────────────────────────────
        POR QUE `_arredondar` E NÃO `round()`
        ─────────────────────────────────────────────────────────────────────
        `round()` do Python arredonda para o EVEN (2.5 → 2, 3.5 → 4). O
        `Math.round()` do JavaScript, que é o do painel original, arredonda
        para CIMA (2.5 → 3, 3.5 → 4).

        A diferença aparece exatamente nos cenarios: 10 pendentes × 25% dá
        2.5. Com `round()` o relatório em Python diria "2 recuperados" e a
        tela diria "3". Dois números diferentes para o mesmo fato, na
        mesma reunião — que é o tipo de discussão que faz o dado ser
        ignorado. `_arredondar` replica o `Math.round` do painel.
        """
        total = len(atendimentos)
        atual = AuditoriaRecuperacao.taxa_sucesso(atendimentos)
        contagem = AuditoriaRecuperacao.contar(atendimentos)

        pendentes = (
            contagem["critico"]
            + contagem["direcionado"]
            + contagem["robo"]
            + contagem["aguardando"]
        )

        cenarios: List[Dict[str, float | int]] = []
        for fracao in percentuais:
            recuperados = AuditoriaRecuperacao._arredondar(pendentes * fracao)
            # Guarda contra divisão por zero: o cenário é desenhado mesmo
            # num relatório sem nenhum atendimento.
            nova_taxa = round(((contagem["ok"] + recuperados) / total) * 100, 1) if total else 0.0
            cenarios.append(
                {
                    "pct": round(fracao * 100),
                    "recuperados": recuperados,
                    "nova_taxa": nova_taxa,
                    "delta_pp": round(nova_taxa - atual, 1),
                }
            )
        return cenarios

    @staticmethod
    def _arredondar(valor: float) -> int:
        """
        Arredonda para cima em caso de empate — igual ao `Math.round`.

        `math.floor(valor + 0.5)` em vez do `round()` nativo. A diferença
        só aparece em `.5` exato, que é justamente o caso dos percentuais
        de cenário sobre contagens pequenas. Ver `cenarios`.
        """
        return int(math.floor(valor + 0.5))

    @staticmethod
    def gerar_indicadores(
        atendimentos: Sequence["AtendimentoRelatorioDTO"],
    ) -> Dict[str, object]:
        """
        Monta o pacote de indicadores do relatório.

        ─────────────────────────────────────────────────────────────────────
        POR QUE UM DICTIONÁRIO E NÃO UM OBJETO
        ─────────────────────────────────────────────────────────────────────
        Porque este dicionário vai direto para `_TEMPLATE_AUDITORIA.format(...)`
        e depois para `json.dumps` no JavaScript do relatório. Um objeto
        exigiria conversão campo a campo na fronteira — e é na fronteira
        que se esquece de um campo e o gráfico sai vazio sem erro.
        """
        contagem = AuditoriaRecuperacao.contar(atendimentos)

        return {
            "total": len(atendimentos),
            "critico": contagem["critico"],
            "direcionado": contagem["direcionado"],
            "robo": contagem["robo"],
            "aguardando": contagem["aguardando"],
            "ok": contagem["ok"],
            "pendencias": (
                contagem["critico"]
                + contagem["direcionado"]
                + contagem["robo"]
                + contagem["aguardando"]
            ),
            "taxa_sucesso": AuditoriaRecuperacao.taxa_sucesso(atendimentos),
            "cenarios": AuditoriaRecuperacao.cenarios(atendimentos),
        }

    # ─────────────────────────────────────────────────────────────────────
    # CRITICIDADE POR TEMPO
    # ─────────────────────────────────────────────────────────────────────

    @staticmethod
    def criticidade(
        minutos: float | None,
        *,
        agora: datetime | None = None,
    ) -> Dict[str, str]:
        """
        Classifica a urgência de uma pendência pelo tempo em aberto.

        ─────────────────────────────────────────────────────────────────────
        AS FAIXAS, E POR QUE ESTES NÚMEROS
        ─────────────────────────────────────────────────────────────────────
            < 30 min   OK        a pessoa ainda está comeendo
            < 60 min   Atenção    passou do almoço
            < 180 min  Moderado   3h — quase um turno
            < 360 min  Alto      6h — turno cheio
            ≥ 360 min  Crítico   passou-se o expediente

        Não são arbitrários: 30 minutos é o que o cliente tolera antes de
        concluir que foi ignorado; 6 horas é a jornada. Os números são de
        resposta humana, não de métrica de software.

        ─────────────────────────────────────────────────────────────────────
        POR QUE `minutos is None` VAI PRIMEIRO
        ─────────────────────────────────────────────────────────────────────
        `None` significa data de criação ilegível. Sem este teste, `None`
        passaria como `< 30` e um registro ilegível apareceria como "OK" —
        o erro mais perigoso possível num relatório de perda.
        """
        if minutos is None or minutos < 0:
            return {
                "nivel": "desconhecido",
                "rotulo": "—",
                "cor": "#78716c",
                "fundo": "#f4f0ed",
            }

        if minutos < 30:
            nivel, rotulo, cor, fundo = "ok", "OK", "#22c55e", "#f0fdf4"
        elif minutos < 60:
            nivel, rotulo, cor, fundo = "atencao", "Atenção", "#86efac", "#f0fdf4"
        elif minutos < 180:
            nivel, rotulo, cor, fundo = "moderado", "Moderado", "#f59e0b", "#fffbeb"
        elif minutos < 360:
            nivel, rotulo, cor, fundo = "alto", "Alto", "#f97316", "#fff7ed"
        else:
            nivel, rotulo, cor, fundo = "critico", "Crítico", "#ef4444", "#fff0f2"

        return {"nivel": nivel, "rotulo": rotulo, "cor": cor, "fundo": fundo}


# ─────────────────────────────────────────────────────────────────────────────
# BLOCO 1 — A PORTA DE ENTRADA
# ─────────────────────────────────────────────────────────────────────────────
# Estas funções existem porque `relatorio_service` as importa por nome. A
# regra mora toda na classe acima; aqui não há lógica, apenas o contrato
# que o outro módulo já consome. Duplicar a lógica aqui faria as duas
# versões divergirem na primeira correção — e a que sobraria errada seria
# a do relatório.


def classificar_pendencia(atendimento: "AtendimentoRelatorioDTO") -> ClassificacaoPendencia:
    """
    Classifica um atendimento na auditoria de recuperação.

    Delega para `AuditoriaRecuperacao.classificar`. Ver a tabela de
    decisão na docstring do método.
    """
    return AuditoriaRecuperacao.classificar(atendimento)


def gerar_indicadores(
    atendimentos: Sequence["AtendimentoRelatorioDTO"],
) -> Dict[str, object]:
    """
    Gera o pacote de indicadores do relatório de auditoria.

    Devolve, no mínimo, as chaves `taxa_sucesso` e `cenarios` — são as
    duas que `_TEMPLATE_AUDITORIA` formata.
    """
    return AuditoriaRecuperacao.gerar_indicadores(atendimentos)


__all__ = [
    "AuditoriaRecuperacao",
    "ClassificacaoPendencia",
    "classificar_pendencia",
    "gerar_indicadores",
    "PERCENTUAIS_CENARIO",
]
