"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-MA · Arquivo
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     arquivo_models.py
@module   Backend / App / Models / Arquivo
@author   Aldemir Queiroz
@since    2026
@version  1.0.0
───────────────────────────────────────────────────────────────────────────

FUNCIONALIDADE
──────────────
Biblioteca de mídia da empresa. `Arquivo` guarda os binários que o chatbot
envia e recebe: fotos de perfil, documentos, áudios de resposta, imagens de
menu, planilhas e PDF de relatório.

A ideia é simples e vale deixar explícita: a empresa **não contracted um
canal, ela usa o EcoChatBot-MA**. O arquivo é da empresa, não do WhatsApp,
do Telegram ou do PABX. Se a mesma empresa contratar dez canais, o mesmo
arquivo continua valendo nos dez. Por isso a FK é `empresa_id` (via
`TenantMixin`) e nunca `canal_id`.

EXEMPLO PRÁTICO
───────────────
    Cliente manda uma foto pelo WhatsApp
        → Arquivo(nome_original="recibo.jpg",
                   nome_arquivo="tenant_7/2026/10/a1b2c3.jpg",
                   tipo_mime="image/jpeg",
                   empresa_id=7,
                   atendimento_id=1540)

    O bot responde com a mesma foto no Telegram
        → mesmo Arquivo, outro CanalContratado

RELACIONAMENTO
──────────────
    Empresa (1) ── (N) Arquivo
    Atendimento (1) ── (N) Arquivo        [opcional]

    · `empresa_id`   vem do `TenantMixin` e é o filtro Anti-IDOR de TODA
      query. Um arquivo sem empresa é um arquivo de ninguém — não existe.
    · `atendimento_id` é NULLABLE de propósito: o mesmo arquivo serve a
      muitos atendimentos (uma foto de capa, um catálogo) e não deve ser
      duplicado por atendido. Quando preenchido, o arquivo nasceu naquele
      atendimento.

    Objetos relacionados (nenhum é dependência deste model):
        Empresa      → dona da biblioteca           (tenant)
        Atendimento  → contexto opcional do arquivo
        CanalContratado → NÃO se relaciona. O canal é a TECNOLOGIA de
                        entrada; o arquivo é conteúdo, não porta de entrada.

REGRAS DE NEGÓCIO
─────────────────
    • `nome_original` é o que o usuário chamou. Serve para exibir.
    • `nome_arquivo` é o caminho real no armazenamento, e precisa ser único
      por empresa. Dois tenants podem ter dois "recibo.jpg" sem conflito,
      porque o prefixo do tenant entra no caminho.
    • `tamanho_bytes` é INTEGER porque o limite é de espaço em disco, não
      de megabyte: conta bytes, não "MB".
    • Soft delete: apagar arquivo NÃO apaga o histórico. Um atendimento
      encerrado há dois anos precisa continuar auditável, e a resposta que
      o cliente recebeu aponta para o mesmo registro.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import SoftDeleteMixin, TenantMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.atendimento_models import Atendimento
    from app.models.empresa_models import Empresa


class Arquivo(TimestampMixin, SoftDeleteMixin, TenantMixin, Base):
    """
    Arquivo da biblioteca de mídia de uma empresa.

    ─────────────────────────────────────────────────────────────────────
    POR QUE HERDA TRÊS MIXINS
    ─────────────────────────────────────────────────────────────────────
        TimestampMixin  → `criado_em` / `atualizado_em`. Sem isso não dá
                           para responder "o que existed há 30 dias".
        SoftDeleteMixin → `deleted_at`. O arquivo some da lista, o registro
                           fica. Apagar de vez quebraria a auditoria.
        TenantMixin     → `empresa_id`. Todo acesso passa por ele; é o que
                           impede a empresa A de ler a mídia da empresa B.

    ─────────────────────────────────────────────────────────────────────
    POR QUE `atendimento_id` É NULLABLE
    ─────────────────────────────────────────────────────────────────────
    O mesmo arquivo atende a vários atendimentos. Se o FK fosse NOT NULL,
    a biblioteca da empresa (catálogo, capa, logo) não caberia no modelo —
    e modelar a biblioteca como N arquivos órfãos seria o caminho errado.
    NULLABLE diz: "pode ter contexto, mas não depende dele".
    """

    __tablename__ = "arquivos"

    #: Chave primária. O `id` é sobrescrito aqui porque os mixins já
    #: definem as demais colunas e a ordem de resolução MRO é o que
    #: garante que todas apareçam na tabela.
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # ─── O arquivo como o usuário o conhece ───────────────────────────────
    nome_original: Mapped[str] = mapped_column(
        String(200), nullable=False,
        comment='Nome enviado pelo usuário — ex.: "recibo.jpg"',
    )
    nome_arquivo: Mapped[str] = mapped_column(
        String(300), nullable=False, index=True,
        comment="Caminho real no armazenamento — único por empresa",
    )

    # ─── Metadados técnicos ───────────────────────────────────────────────
    tipo_mime: Mapped[str | None] = mapped_column(
        String(100), index=True,
        comment='MIME type — ex.: "image/jpeg", "application/pdf"',
    )
    tamanho_bytes: Mapped[int | None] = mapped_column(
        Integer,
        comment="Tamanho em BYTES (não MB) — o limite real é de disco",
    )

    # ─── Contexto humano ──────────────────────────────────────────────────
    descricao: Mapped[str | None] = mapped_column(
        Text,
        comment="Descrição libre — aparece na listagem da biblioteca",
    )

    # ─── Vínculo opcional com o atendimento ───────────────────────────────
    atendimento_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("atendimentos.id", ondelete="SET NULL"),
        nullable=True, index=True,
        comment=(
            "NULLABLE: o mesmo arquivo serve a N atendimentos. "
            "ON DELETE SET NULL preserva o arquivo se o atendimento cair."
        ),
    )

    # ─── Relacionamentos ──────────────────────────────────────────────────
    #
    # `empresa` NÃO tem back_populates: `Empresa` é legado e não declara
    # a relação. Desenhar dos dois lados exigiria mexer no model de Empresa,
    # que tem duplicação própria. Fica a FK + filtro por `empresa_id`, que é
    # o que realmente garante o isolamento multi-tenant.
    empresa: Mapped["Empresa"] = relationship()

    atendimento: Mapped["Atendimento | None"] = relationship(
        back_populates="arquivos",
    )

    # ─────────────────────────────────────────────────────────────────────
    # PROPRIEDADES DERIVADAS
    # ─────────────────────────────────────────────────────────────────────
    # Não são colunas: são respostas que a camada de serviço e o frontend
    # pedem o tempo todo. Decoradas com @property porque em POO o comportamento
    # mora na classe, e não em função solta na camada de cima.

    @property
    def extensao(self) -> str:
        """Extensão do arquivo em minúsculas, sem o ponto — ex.: `"pdf"`."""
        nome = self.nome_original or ""
        if "." not in nome:
            return ""
        return nome.rsplit(".", 1)[-1].lower()

    @property
    def tamanho_legivel(self) -> str:
        """
        Tamanho em unidade legível, para exibir na tela.

        O valor cru em bytes fica intacto no banco — nunca se formata dado
        para guardar. A formatação é sempre na leitura.
        """
        if self.tamanho_bytes is None:
            return "—"
        tamanho = float(self.tamanho_bytes)
        for unidade in ("B", "KB", "MB", "GB"):
            if tamanho < 1024 or unidade == "GB":
                return f"{tamanho:.0f} {unidade}" if unidade == "B" else f"{tamanho:.1f} {unidade}"
            tamanho /= 1024
        return f"{tamanho:.1f} GB"

    @property
    def eh_imagem(self) -> bool:
        """True quando a mídia é imagem — usada para decidir miniatura."""
        return bool(self.tipo_mime and self.tipo_mime.startswith("image/"))

    @property
    def disponivel(self) -> bool:
        """
        Arquivo utilizável agora.

        Um arquivo com soft delete tem histórico válido e ainda aparece na
        auditoria do atendimento, mas não deve ser oferecida como anexo
        novo. Esta propriedade separa as duas coisas sem apagar o registro.
        """
        return self.deleted_at is None

    # ─────────────────────────────────────────────────────────────────────
    # COMPORTAMENTO
    # ─────────────────────────────────────────────────────────────────────

    def descrever(self, descricao: str) -> None:
        """
        Define a descrição do arquivo.

        Método e não atribuição direta porque a regra "não sobrescrever
        descrição com string vazia" é do domínio: limpar por engano num
        formulário é mais comum do que se imagina.
        """
        if descricao and descricao.strip():
            self.descricao = descricao.strip()

    def arquivar(self) -> None:
        """
        Soft delete: some da biblioteca, preserva o histórico.

        Deliberadamente não apaga a linha. Um atendimento encerrado precisa
        continuar auditável, e a resposta que o cliente recebeu aponta para
        este mesmo registro.
        """
        from datetime import datetime, timezone

        self.deleted_at = datetime.now(timezone.utc)

    def __repr__(self) -> str:
        return (
            f"<Arquivo id={self.id} nome_original={self.nome_original!r} "
            f"tipo_mime={self.tipo_mime!r} empresa_id={self.empresa_id}>"
        )


__all__ = ["Arquivo"]
