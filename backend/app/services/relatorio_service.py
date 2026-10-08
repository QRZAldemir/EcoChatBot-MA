"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-MA · relatorio_service
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     relatorio_service.py
@module   Backend / app/services
@author   Aldemir Queiroz
@since    2026
@version  1.0.0
───────────────────────────────────────────────────────────────────────────

=============================================================================
ARQUIVO: backend/app/services/relatorio_service.py
CAMADA:  Serviço (regras de negócio de relatório)
PROJETO: EcoChatBot-MA - Omnichannel SaaS
MÓDULO: services/pabx_service.py
AUTOR: Aldemir Queiroz
CONTATO: [Inserir E-mail] | [Inserir LinkedIn] | [Inserir GitHub]
DATA: 2024-05-20
=============================================================================
RESPONSABILIDADE:
    - Calcular tempos de espera/atendimento a partir de `criado_em` /
      `finalizado_em`.
    - Derivar o status canônico dos atendimentos (mesma precedência usada
      pelo frontend Angular).
    - Construir DataFrame no layout EXATO da planilha RLT_ATENDIMENTO_atual.
    - Exportar .xlsx (openpyxl), HTML analítico (Chart.js) e HTML de
      auditoria de recuperação.
    - Fornecer dados agregados para os endpoints de /relatorios e /auditoria.

RELAÇÃO COM OUTRAS CAMADAS:
    - Lê do ORM          -> backend/app/models/atendimento_model.py
    - Reutiliza schemas  -> backend/app/schemas/atendimento_schema.py
    - É consumido por    -> backend/app/routers/relatorios.py (endpoints)
    - É consumido por    -> backend/gerar_relatorio.py (CLI)
    - Alimenta o frontend Angular (interface `AtendimentoRelatorio` em
      frontend/src/app/core/models/atendimento-relatorio.model.ts)
    - Reutiliza auditoria_service.py para classificação de pendências.

CONVENÇÕES:
    - Tipagem estrita (PEP 604: `str | None`), sem uso de `Any` solto.
    - Funções puras primeiro; efeitos colaterais (I/O) isolados no fim.
    - Datas: sempre UTC internamente; formatação BR apenas na borda.
=============================================================================
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, Literal, Sequence

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

# Classificação de pendências usada na auditoria (módulo irmão)
from app.services.auditoria_service import (
    ClassificacaoPendencia,
    classificar_pendencia,
    gerar_indicadores,
)

# =============================================================================
# BLOCO 0 — TIPOS E CONSTANTES
# =============================================================================

# Tipo literal aceito pelo CLI/endpoints. Garante cobertura em tempo de tipo.
FormatoSaida = Literal["xlsx", "analitico-html", "auditoria-html", "todos"]

# Rótulos canônicos de status. Espelham:
#   - backend/app/schemas/atendimento_schema.py (enum do Pydantic)
#   - frontend/.../relatorio.component.ts (getStatusBadge)
STATUS_AGUARDANDO: str = "Aguardando"
STATUS_FINALIZADO_SEM_ATENDIMENTO: str = "Finalizado s/ Atendimento"
STATUS_NAO_FINALIZADO: str = "Não Finalizado"

# Cabeçalho OFICIAL da planilha. Fonte única da verdade.
CABECALHO_OFICIAL: tuple[str, ...] = (
    "Protocolo",
    "Conexão/ID_EMPRESA",
    "Criação",
    "Finalização",
    "Cód. cli",
    "Nome",
    "Nasc.",
    "Telefone",
    "Obs.",
    "Atendente/Usuário",
    "Tag",
    "Iniciado por",
    "Data_Abertura",
    "Hora_Abertura",
    "Data_Finalização",
    "Hora_Finalização",
    "Status_Atendimento",
    "Tempo_Espera_Min",
    "Tempo_Espera_Fmt",
    "FINALIZADOSEMATENDIMENTO",
    "AguardandoAtendimento",
)

# Limite (horas) para "Pendência Prolongada" — regra documentada no README §10.
LIMITE_PENDENCIA_HORAS: int = 24


@dataclass(frozen=True)
class AtendimentoRelatorioDTO:
    """
    DTO interno que espelha 1:1 a interface TypeScript `AtendimentoRelatorio`.
    Usar dataclass (em vez de dict) garante tipagem forte dentro do service.
    """
    protocolo: str
    conexao_id_empresa: str
    criacao: datetime
    finalizacao: datetime | None
    cod_cliente: str
    nome_cliente: str
    telefone: str
    atendente_usuario: str | None
    tag: str | None
    status_atendimento: str
    finalizado_sem_atendimento: bool
    aguardando_atendimento: bool
    # Campos extras usados apenas internamente (não vão ao frontend):
    iniciado_por: str = "cliente"
    nascimento: str | None = None
    observacao: str | None = None
    departamento_nome: str | None = None


# =============================================================================
# BLOCO 1 — FUNÇÕES PURAS DE TEMPO
# =============================================================================

def _agora_utc() -> datetime:
    """Wrapper isolado para facilitar mock em testes."""
    return datetime.now(timezone.utc)


def _como_utc(dt: datetime) -> datetime:
    """
    Normaliza um datetime para UTC com fuso.

    ─────────────────────────────────────────────────────────────────────
    POR QUE ISTO É NECESSÁRIO
    ─────────────────────────────────────────────────────────────────────
    A coluna `criacao` é `DateTime` SEM `timezone=True`, então o SQLAlchemy
    devolve datetime *naive*. Já `_agora_utc()` devolve *aware*. Subtrair um
    do outro levanta `TypeError: can't subtract offset-naive and
    offset-aware datetimes` — e o relatório inteiro morre no primeiro
    atendimento.

    Tratar o naive como UTC é seguro porque é assim que a aplicação grava:
    todo `datetime.now()` do serviço passa por UTC antes de persistir.
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def calcular_tempo_espera_min(
    criado_em: datetime,
    finalizado_em: datetime | None = None,
    *,
    agora: datetime | None = None,
) -> float | None:
    """
    Calcula o tempo de espera em minutos.

    REGRA (README §10):
        - Finalizado  -> finalizado_em - criado_em
        - Em aberto   -> agora - criado_em   (cálculo em tempo real)

    O parâmetro `agora` existe para permitir testes determinísticos.

    ─────────────────────────────────────────────────────────────────────
    POR QUE NUNCA DEVOLVER NEGATIVO
    ─────────────────────────────────────────────────────────────────────
    Relógio de servidor adiantado, ou dado digitado errado, produz
    finalização anterior à criação. O resultado negativo é impossível de
    explicar para um gestor ("esperou -5 minutos?"), então o piso é 0.
    """
    if criado_em is None:
        return None
    referencia = finalizado_em if finalizado_em else (agora or _agora_utc())
    delta: timedelta = _como_utc(referencia) - _como_utc(criado_em)
    return round(max(0.0, delta.total_seconds() / 60), 2)


def formatar_tempo_espera(minutos: float | None) -> str | None:
    """
    Converte minutos para o formato humano "Xh Ymin".

    ─────────────────────────────────────────────────────────────────────
    POR QUE OMITE "0h"
    ─────────────────────────────────────────────────────────────────────
    Porque é o que o `fmtMin` do gráfico já faz (`h>0 ? ... : mn+'min'`).
    Sem essa alinhagem, uma espera de 45 minutos aparecia "0h 45min" na
    tabela e "45min" no tooltip do gráfico — o mesmo número com duas
    grafias na mesma tela, na mesma reunião.
    """
    if minutos is None or minutos < 0:
        return None
    horas = int(minutos // 60)
    mins = int(minutos % 60)
    if horas == 0:
        return f"{mins}min"
    return f"{horas}h {mins}min"


def derivar_status(
    status_atendimento: str | None,
    *,
    aguardando: bool,
    finalizado_sem_atendimento: bool,
) -> str:
    """
    Deriva o status canônico seguindo a MESMA precedência do Angular.

    PRECEDÊNCIA (ordem importa):
        1. aguardando_atendimento = True  -> 'Aguardando'
        2. finalizado_sem_atendimento     -> 'Finalizado s/ Atendimento'
        3. Caso contrário                 -> status_atendimento original
    """
    if aguardando:
        return STATUS_AGUARDANDO
    if finalizado_sem_atendimento:
        return STATUS_FINALIZADO_SEM_ATENDIMENTO
    return status_atendimento or STATUS_NAO_FINALIZADO


# =============================================================================
# BLOCO 2 — CLASSE DE SERVIÇO
# =============================================================================

class RelatorioService:
    """
    Serviço de geração de relatórios. Métodos estáticos para facilitar uso
    via CLI e injeção via FastAPI sem instanciar.
    """

    # -------------------------------------------------------------------
    # 2.1 — Construção do DataFrame (camada de mapeamento ORM -> planilha)
    # -------------------------------------------------------------------
    @staticmethod
    def construir_dataframe(
        atendimentos: Sequence[AtendimentoRelatorioDTO],
        *,
        agora: datetime | None = None,
    ) -> pd.DataFrame:
        """
        Recebe a lista tipada de atendimentos e devolve DataFrame com as
        21 colunas oficiais, na ordem exata.
        """
        momento = agora or _agora_utc()
        linhas: list[dict[str, object]] = []

        for at in atendimentos:
            minutos = calcular_tempo_espera_min(
                criado_em=at.criacao,
                finalizado_em=at.finalizacao,
                agora=momento,
            )
            minutos_fmt = formatar_tempo_espera(minutos)
            status = derivar_status(
                at.status_atendimento,
                aguardando=at.aguardando_atendimento,
                finalizado_sem_atendimento=at.finalizado_sem_atendimento,
            )

            # Formatação BR (borda do sistema — o resto trafega em UTC)
            data_abertura = at.criacao.strftime("%d/%m/%Y")
            hora_abertura = at.criacao.strftime("%H:%M")
            if at.finalizacao:
                data_fim = at.finalizacao.strftime("%d/%m/%Y")
                hora_fim = at.finalizacao.strftime("%H:%M")
            else:
                data_fim, hora_fim = "Não Finalizado", ""

            linhas.append({
                "Protocolo": at.protocolo,
                "Conexão/ID_EMPRESA": at.conexao_id_empresa,
                "Criação": at.criacao.strftime("%d/%m/%Y %H:%M"),
                "Finalização": (
                    at.finalizacao.strftime("%d/%m/%Y %H:%M")
                    if at.finalizacao else "Não finalizado"
                ),
                "Cód. cli": at.cod_cliente,
                "Nome": at.nome_cliente,
                "Nasc.": at.nascimento or "",
                "Telefone": at.telefone,
                "Obs.": at.observacao or "",
                "Atendente/Usuário": at.atendente_usuario or "",
                "Tag": at.tag or "",
                "Iniciado por": at.iniciado_por.capitalize(),
                "Data_Abertura": data_abertura,
                "Hora_Abertura": hora_abertura,
                "Data_Finalização": data_fim,
                "Hora_Finalização": hora_fim,
                "Status_Atendimento": status,
                "Tempo_Espera_Min": minutos,
                "Tempo_Espera_Fmt": minutos_fmt,
                "FINALIZADOSEMATENDIMENTO": "S" if at.finalizado_sem_atendimento else "N",
                "AguardandoAtendimento": "S" if at.aguardando_atendimento else "N",
            })

        return pd.DataFrame(linhas, columns=list(CABECALHO_OFICIAL))

    # -------------------------------------------------------------------
    # 2.2 — Exportação .xlsx (formato 1)
    # -------------------------------------------------------------------
    @staticmethod
    def exportar_excel(df: pd.DataFrame, caminho_saida: Path) -> Path:
        """
        Exporta o DataFrame para .xlsx com cabeçalho estilizado.
        Mantém o layout visual já conhecido pelo time.
        """
        wb = Workbook()
        ws = wb.active
        ws.title = "Dados Unificados"

        header_font = Font(bold=True, color="FFFFFF", size=11)
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
        borda = Border(
            left=Side(style="thin"), right=Side(style="thin"),
            top=Side(style="thin"), bottom=Side(style="thin"),
        )

        for idx, nome in enumerate(df.columns, start=1):
            c = ws.cell(row=1, column=idx, value=nome)
            c.font, c.fill, c.alignment, c.border = header_font, header_fill, header_align, borda

        for r_idx, linha in enumerate(df.itertuples(index=False), start=2):
            for c_idx, valor in enumerate(linha, start=1):
                c = ws.cell(row=r_idx, column=c_idx, value=valor)
                c.border = borda

        for idx, nome in enumerate(df.columns, start=1):
            letra = get_column_letter(idx)
            maior = max([len(str(nome))] + [len(str(v)) for v in df.iloc[:, idx - 1]])
            ws.column_dimensions[letra].width = max(12, min(maior + 2, 40))

        caminho_saida.parent.mkdir(parents=True, exist_ok=True)
        wb.save(caminho_saida)
        return caminho_saida

    # -------------------------------------------------------------------
    # 2.3 — Exportação HTML analítico (formato 2)
    # -------------------------------------------------------------------
    @staticmethod
    def _agregar_por_departamento(
        atendimentos: Sequence[AtendimentoRelatorioDTO],
    ) -> list[dict[str, object]]:
        """
        Agrega total / finalizados / abertos por departamento.
        Retorna lista já pronta para o Chart.js do HTML analítico.
        """
        bucket: dict[str, dict[str, int]] = {}
        for at in atendimentos:
            chave = at.departamento_nome or "Sem Depto"
            b = bucket.setdefault(chave, {"total": 0, "fin": 0, "aberto": 0})
            b["total"] += 1
            if at.finalizacao:
                b["fin"] += 1
            else:
                b["aberto"] += 1

        return [
            {"departamento": k, **v}
            for k, v in sorted(bucket.items(), key=lambda kv: -kv[1]["total"])
        ]

    @staticmethod
    def _agregar_tma_por_atendente(
        atendimentos: Sequence[AtendimentoRelatorioDTO],
    ) -> list[dict[str, object]]:
        """
        TMA (Tempo Médio de Atendimento) por atendente — apenas finalizados.
        Usado no gráfico horizontal do HTML analítico.
        """
        bucket: dict[str, list[float]] = {}
        for at in atendimentos:
            if not at.finalizacao or not at.atendente_usuario:
                continue
            minutos = calcular_tempo_espera_min(at.criacao, at.finalizacao)
            if minutos is not None:
                bucket.setdefault(at.atendente_usuario, []).append(minutos)

        resultado: list[dict[str, object]] = []
        for nome, valores in bucket.items():
            resultado.append({
                "atendente": nome,
                "tma": round(sum(valores) / len(valores), 1),
                "qtd": len(valores),
            })
        return sorted(resultado, key=lambda x: -x["tma"])

    @staticmethod
    def exportar_html_analitico(
        atendimentos: Sequence[AtendimentoRelatorioDTO],
        caminho_saida: Path,
        *,
        periodo_label: str,
    ) -> Path:
        """
        Gera o HTML analítico (port do Rtl_Analitico_30-09-2026.html).
        Estrutura: indicadores gerais, gráficos Chart.js, tabelas por
        departamento e desempenho por atendente.
        """
        total = len(atendimentos)
        finalizados = sum(1 for a in atendimentos if a.finalizacao)
        abertos = total - finalizados

        por_dep = RelatorioService._agregar_por_departamento(atendimentos)
        por_atendente = RelatorioService._agregar_tma_por_atendente(atendimentos)

        # Tempo médio geral (apenas finalizados)
        temps = [
            calcular_tempo_espera_min(a.criacao, a.finalizacao)
            for a in atendimentos if a.finalizacao
        ]
        temps_validos = [t for t in temps if t is not None]
        tma_medio = round(sum(temps_validos) / len(temps_validos), 1) if temps_validos else 0

        # Payloads que o Chart.js consome (substituem os `window._gData*` antigos)
        g_data_atend = {
            "labels": [d["departamento"] for d in por_dep],
            "total": [d["total"] for d in por_dep],
            "fin": [d["fin"] for d in por_dep],
            "aberto": [d["aberto"] for d in por_dep],
        }
        g_data_tma = {
            "labels": [a["atendente"] for a in por_atendente],
            "tmas": [a["tma"] for a in por_atendente],
            "qtds": [a["qtd"] for a in por_atendente],
        }

        linhas_dep = "".join(
            f"<tr><td><strong>{d['departamento']}</strong></td>"
            f"<td style='text-align:center'>{d['total']}</td>"
            f"<td style='text-align:center;color:#15803d'>{d['fin']}</td>"
            f"<td style='text-align:center;color:#78716c'>{d['aberto']}</td>"
            f"<td>{round(d['fin']/d['total']*100) if d['total'] else 0}%</td></tr>"
            for d in por_dep
        )
        linhas_atendente = "".join(
            f"<tr><td><strong>{a['atendente']}</strong></td>"
            f"<td style='text-align:center'>{a['qtd']}</td>"
            f"<td style='text-align:right'>{formatar_tempo_espera(a['tma']) or '—'}</td></tr>"
            for a in por_atendente
        )

        html = _TEMPLATE_ANALITICO.format(
            periodo=periodo_label,
            gerado_em=datetime.now().strftime("%d/%m/%Y, %H:%M:%S"),
            total=total,
            finalizados=finalizados,
            abertos=abertos,
            tma_medio=formatar_tempo_espera(tma_medio) or "—",
            linhas_dep=linhas_dep,
            linhas_atendente=linhas_atendente,
            g_data_atend=json.dumps(g_data_atend, ensure_ascii=False),
            g_data_tma=json.dumps(g_data_tma, ensure_ascii=False),
        )

        caminho_saida.parent.mkdir(parents=True, exist_ok=True)
        caminho_saida.write_text(html, encoding="utf-8")
        return caminho_saida

    # -------------------------------------------------------------------
    # 2.4 — Exportação HTML de auditoria (formato 3)
    # -------------------------------------------------------------------
    @staticmethod
    def exportar_html_auditoria(
        atendimentos: Sequence[AtendimentoRelatorioDTO],
        caminho_saida: Path,
        *,
        periodo_label: str,
    ) -> Path:
        """
        Gera o HTML de auditoria de recuperação (port do
        auditoria-recuperacao.html). Reutiliza `auditoria_service` para
        classificar cada atendimento nos 4 tipos de pendência.
        """
        grupos: dict[ClassificacaoPendencia, list[AtendimentoRelatorioDTO]] = {
            "critico": [], "direcionado": [], "robo": [], "aguardando": [], "ok": [],
        }
        for at in atendimentos:
            grupos[classificar_pendencia(at)].append(at)

        indicadores = gerar_indicadores(list(atendimentos))

        def _tabela(itens: Iterable[AtendimentoRelatorioDTO], tipo: str) -> str:
            linhas = []
            for at in itens:
                minutos = calcular_tempo_espera_min(at.criacao, at.finalizacao)
                tempo_fmt = formatar_tempo_espera(minutos) or "—"
                depto = at.departamento_nome or "Sem Departamento"
                criado = at.criacao.strftime("%d/%m/%y, %H:%M")
                linhas.append(
                    f"<tr><td><strong>{at.nome_cliente}</strong></td>"
                    f"<td>{depto}</td><td>{at.telefone}</td>"
                    f"<td>{at.protocolo}</td><td>{criado}</td>"
                    f"<td>{at.iniciado_por.capitalize()}</td>"
                    f"<td>{tempo_fmt}</td>"
                    f"<td><span class='respcol' contenteditable='true'>&nbsp;</span></td>"
                    f"<td><span class='respcol' contenteditable='true' style='min-width:220px'>&nbsp;</span></td></tr>"
                )
            return "".join(linhas) if linhas else "<tr><td colspan='9'>Nenhum registro.</td></tr>"

        def _tabela_cenarios(cenarios: Iterable[dict]) -> str:
            """
            Monta as linhas da tabela de cenários no SERVIDOR.

            ─────────────────────────────────────────────────────────────────────
            POR QUE NÃO CONSTRUIR ISSO EM JAVASCRIPT
            ─────────────────────────────────────────────────────────────────────
            Porque este relatório é anexo de e-mail. Cliente de e-mail
            remove `<script>` por padrão — um gráfico montado em JS
            chegaria ao gestor em branco, sem aviso nenhum. A barra é CSS
            puro dentro da célula, então sobrevive a e-mail, PDF e
            navegador.

            É a diferença entre "o relatório chegou" e "o relatório chegou
            com um buraco onde deveria ter o número".
            """
            linhas = []
            for c in cenarios:
                pct = float(c["pct"])
                nova = float(c["nova_taxa"])
                delta = float(c["delta_pp"])
                linhas.append(
                    f"<tr><td><strong>+{pct:.0f}%</strong></td>"
                    f"<td>{c['recuperados']}</td>"
                    f"<td style='width:42%'>"
                    f"<div class='bar'><div class='fill' style='width:{nova:.1f}%'></div></div>"
                    f"<strong>{nova:.1f}%</strong></td>"
                    f"<td>+{delta:.1f} p.p.</td></tr>"
                )
            return "".join(linhas) if linhas else "<tr><td colspan='4'>Nenhum cenário.</td></tr>"

        html = _TEMPLATE_AUDITORIA.format(
            periodo=periodo_label,
            gerado_em=datetime.now().strftime("%d/%m/%Y, %H:%M:%S"),
            n_critico=len(grupos["critico"]),
            n_direcionado=len(grupos["direcionado"]),
            n_robo=len(grupos["robo"]),
            n_aguardando=len(grupos["aguardando"]),
            taxa_sucesso=f"{indicadores['taxa_sucesso']:.1f}%",
            linhas_critico=_tabela(grupos["critico"], "critico"),
            linhas_direcionado=_tabela(grupos["direcionado"], "direcionado"),
            linhas_robo=_tabela(grupos["robo"], "robo"),
            linhas_aguardando=_tabela(grupos["aguardando"], "aguardando"),
            linhas_cenarios=_tabela_cenarios(indicadores["cenarios"]),
        )

        caminho_saida.parent.mkdir(parents=True, exist_ok=True)
        caminho_saida.write_text(html, encoding="utf-8")
        return caminho_saida

    # -------------------------------------------------------------------
    # 2.5 — Orquestrador: gera todos os formatos de uma vez
    # -------------------------------------------------------------------
    @staticmethod
    def gerar_todos(
        atendimentos: Sequence[AtendimentoRelatorioDTO],
        pasta_saida: Path,
        *,
        periodo_label: str,
    ) -> dict[str, Path]:
        """
        Gera os 3 artefatos em uma única chamada. Retorna dict com os
        caminhos para log/CLI.
        """
        pasta_saida.mkdir(parents=True, exist_ok=True)
        agora = _agora_utc()

        df = RelatorioService.construir_dataframe(atendimentos, agora=agora)

        return {
            "xlsx": RelatorioService.exportar_excel(
                df, pasta_saida / "RLT_ATENDIMENTO_atual.xlsx",
            ),
            "analitico": RelatorioService.exportar_html_analitico(
                atendimentos, pasta_saida / "Rtl_Analitico.html",
                periodo_label=periodo_label,
            ),
            "auditoria": RelatorioService.exportar_html_auditoria(
                atendimentos, pasta_saida / "Auditoria_Recuperacao.html",
                periodo_label=periodo_label,
            ),
        }


# =============================================================================
# BLOCO 3 — TEMPLATES HTML (Chart.js + auditoria)
# =============================================================================
# Ficam no fim do módulo para não poluir a leitura da lógica. Os placeholders
# `{}` são preenchidos por `str.format()` nos métodos acima. Chaves literais
# do JavaScript/CSS foram escapadas com `{{` e `}}`.
# =============================================================================

_TEMPLATE_ANALITICO = """<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="UTF-8">
<title>Relatório Analítico — Período: {periodo}</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
body{{font-family:system-ui,sans-serif;background:#f4f0ed;color:#18181b;font-size:13px;margin:0;}}
.wrap{{max-width:980px;margin:0 auto;padding:20px 16px;}}
.sec{{background:#fff;border-radius:12px;border:1px solid #e5ddd8;margin-bottom:18px;overflow:hidden;}}
.sh{{padding:12px 18px;border-bottom:1px solid #e5ddd8;background:#faf9f8;}}
.sh h2{{font-size:13px;margin:0;}}
.bd{{padding:18px;}}
.kgrid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px;margin-bottom:14px;}}
.kc{{background:#faf9f8;border-radius:9px;padding:13px;border-left:4px solid #2563eb;}}
.kc .n{{font-size:26px;font-weight:800;}}
.kc .l{{font-size:10px;color:#78716c;}}
.g2{{display:grid;grid-template-columns:1fr 1fr;gap:14px;}}
.cbox{{background:#faf9f8;border-radius:9px;padding:13px;}}
table{{width:100%;border-collapse:collapse;font-size:12px;}}
th{{padding:8px;background:#faf9f8;font-size:10.5px;text-transform:uppercase;text-align:left;}}
td{{padding:8px;border-bottom:1px solid #f0ece8;}}
</style></head><body>
<div class="wrap">
  <div class="sec"><div class="sh"><h2>Atendimentos — Período: {periodo}</h2></div>
  <div class="bd">
    <div class="kgrid">
      <div class="kc"><div class="n">{total}</div><div class="l">Total Registros</div></div>
      <div class="kc"><div class="n">{finalizados}</div><div class="l">Finalizados</div></div>
      <div class="kc"><div class="n">{abertos}</div><div class="l">Em Aberto</div></div>
      <div class="kc"><div class="n">{tma_medio}</div><div class="l">TMA Médio</div></div>
    </div>
    <div class="g2">
      <div class="cbox"><h4>Volume por Departamento</h4><canvas id="chDept"></canvas></div>
      <div class="cbox"><h4>TMA por Atendente</h4><canvas id="chTMA"></canvas></div>
    </div>
  </div></div>

  <div class="sec"><div class="sh"><h2>Por Departamento</h2></div><div class="bd">
    <table><thead><tr><th>Departamento</th><th>Total</th><th>Finalizados</th><th>Abertos</th><th>Taxa</th></tr></thead>
    <tbody>{linhas_dep}</tbody></table>
  </div></div>

  <div class="sec"><div class="sh"><h2>Desempenho por Atendente</h2></div><div class="bd">
    <table><thead><tr><th>Atendente</th><th>Atendidos</th><th>TMA</th></tr></thead>
    <tbody>{linhas_atendente}</tbody></table>
  </div></div>

  <p style="text-align:center;font-size:10px;color:#a1a1aa">Gerado em {gerado_em} · EcoChatBot-MA</p>
</div>
<script>
window._gDataAtend = {g_data_atend};
window._gDataTMA   = {g_data_tma};
window.addEventListener('load', function() {{
  function fmtMin(m){{if(!m||m<=0)return'—';var h=Math.floor(m/60),mn=Math.round(m%60);return h>0?h+'h '+mn+'min':mn+'min';}}
  if(window._gDataAtend){{
    new Chart(document.getElementById('chDept'),{{type:'bar',data:{{labels:_gDataAtend.labels,datasets:[
      {{label:'Total',data:_gDataAtend.total,backgroundColor:'rgba(37,99,235,.7)'}},
      {{label:'Finalizados',data:_gDataAtend.fin,backgroundColor:'rgba(34,197,94,.8)'}},
      {{label:'Em Aberto',data:_gDataAtend.aberto,backgroundColor:'rgba(220,38,38,.6)'}}
    ]}},options:{{responsive:true,maintainAspectRatio:false,indexAxis:'y'}}}});
  }}
  if(window._gDataTMA){{
    new Chart(document.getElementById('chTMA'),{{type:'bar',data:{{labels:_gDataTMA.labels,datasets:[
      {{label:'TMA',data:_gDataTMA.tmas,backgroundColor:'rgba(245,158,11,.8)'}}
    ]}},options:{{responsive:true,maintainAspectRatio:false,indexAxis:'y',
      tooltip:{{callbacks:{{label:function(c){{return ' '+fmtMin(c.parsed.x);}}}}}}}}}});
  }}
}});
</script></body></html>"""


_TEMPLATE_AUDITORIA = """<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="UTF-8">
<title>Auditoria de Recuperação — Período: {periodo}</title>
<style>
body{{font-family:system-ui,sans-serif;background:#f4f0ed;font-size:13px;margin:0;}}
.wrap{{max-width:1080px;margin:0 auto;padding:20px 16px;}}
.sec{{background:#fff;border-radius:12px;border:1px solid #e5ddd8;margin-bottom:18px;overflow:hidden;}}
.sh{{padding:12px 18px;border-bottom:1px solid #e5ddd8;background:#faf9f8;}}
.sh h2{{font-size:13px;margin:0;}}
.bd{{padding:18px;}}
.kgrid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;}}
.kc{{background:#faf9f8;border-radius:9px;padding:13px;border-left:4px solid;}}
.kc .n{{font-size:26px;font-weight:800;}}
.kc .l{{font-size:10px;color:#78716c;}}
table{{width:100%;border-collapse:collapse;font-size:11.5px;}}
th{{padding:8px;background:#faf9f8;font-size:10px;text-transform:uppercase;text-align:left;}}
td{{padding:8px;border-bottom:1px solid #f0ece8;}}
.respcol{{border:1px dashed #d6d3d1;border-radius:6px;padding:4px 6px;min-width:120px;display:inline-block;}}
.hint{{font-size:11px;color:#78716c;margin:0 0 12px;}}
.bar{{background:#f0ece8;border-radius:999px;height:9px;overflow:hidden;margin-bottom:4px;}}
.fill{{background:linear-gradient(90deg,#2563eb,#15803d);height:100%;border-radius:999px;}}
td[colspan]{{text-align:center;color:#a1a1aa;font-style:italic;}}
</style></head><body>
<div class="wrap">
  <div class="sec"><div class="sh"><h2>Indicadores Gerais</h2></div><div class="bd">
    <div class="kgrid">
      <div class="kc" style="border-color:#ef4444"><div class="n">{n_critico}</div><div class="l">🔴 Crítico</div></div>
      <div class="kc" style="border-color:#9333ea"><div class="n">{n_direcionado}</div><div class="l">🟣 Direcionado Sem Atendimento</div></div>
      <div class="kc" style="border-color:#ea580c"><div class="n">{n_robo}</div><div class="l">🤖 Robô Fechou</div></div>
      <div class="kc" style="border-color:#f59e0b"><div class="n">{n_aguardando}</div><div class="l">🟡 Aguardando Resposta</div></div>
      <div class="kc" style="border-color:#15803d"><div class="n">{taxa_sucesso}</div><div class="l">✅ Taxa de Sucesso</div></div>
    </div>
  </div></div>

  <div class="sec"><div class="sh"><h2>🔴 Tipo 1 — Crítico</h2></div><div class="bd">
    <table><thead><tr><th>Nome</th><th>Departamento</th><th>Telefone</th><th>Protocolo</th><th>Criado em</th><th>Iniciado por</th><th>Tempo</th><th>Responsável</th><th>Observações</th></tr></thead>
    <tbody>{linhas_critico}</tbody></table>
  </div></div>

  <div class="sec"><div class="sh"><h2>🟣 Tipo 2 — Direcionado Sem Atendimento</h2></div><div class="bd">
    <table><thead><tr><th>Nome</th><th>Departamento</th><th>Telefone</th><th>Protocolo</th><th>Criado em</th><th>Iniciado por</th><th>Tempo</th><th>Responsável</th><th>Observações</th></tr></thead>
    <tbody>{linhas_direcionado}</tbody></table>
  </div></div>

  <div class="sec"><div class="sh"><h2>🤖 Tipo 3 — Robô Fechou</h2></div><div class="bd">
    <table><thead><tr><th>Nome</th><th>Departamento</th><th>Telefone</th><th>Protocolo</th><th>Criado em</th><th>Iniciado por</th><th>Tempo</th><th>Responsável</th><th>Observações</th></tr></thead>
    <tbody>{linhas_robo}</tbody></table>
  </div></div>

  <div class="sec"><div class="sh"><h2>🟡 Tipo 4 — Aguardando Resposta</h2></div><div class="bd">
    <table><thead><tr><th>Nome</th><th>Departamento</th><th>Telefone</th><th>Protocolo</th><th>Criado em</th><th>Iniciado por</th><th>Tempo</th><th>Responsável</th><th>Observações</th></tr></thead>
    <tbody>{linhas_aguardando}</tbody></table>
  </div></div>

  <div class="sec"><div class="sh"><h2>📈 Cenários de Recuperação</h2></div><div class="bd">
    <p class="hint">Se o time recuperar parte dos atendimentos pendentes (críticos, direcionados, robô e aguardando), a taxa de sucesso chega a:</p>
    <table><thead><tr><th>Recuperação</th><th>Atendimentos recuperados</th><th>Nova taxa de sucesso</th><th>Ganho</th></tr></thead>
    <tbody>{linhas_cenarios}</tbody></table>
  </div></div>

  <p style="text-align:center;font-size:10px;color:#a1a1aa">Gerado em {gerado_em} · EcoChatBot-MA · Periodo: {periodo}</p>
</div>
</body></html>"""


