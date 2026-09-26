"""
Testes do CanalService contra SQLite assíncrono.

Estes testes exercitam o caminho REAL de execução: `AsyncSession` + `select()`.
Um teste sobre `Session` síncrono passaria mesmo com o serviço quebrado para
async, que foi exatamente o defeito que existia aqui antes.
"""
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import (
    CanalNaoEncontradoError,
    CanalNomeDuplicadoError,
    CanalTipoInvalidoError,
    RecursoInvalidoError,
)
from pydantic import ValidationError

from app.models import Atendimento, Empresa, Telefone
from app.models.enums import StatusAtendimento
from app.schemas.canal_schemas import CanalContratadoCreate, CanalContratadoUpdate
from app.services.canal_service import CanalService


@pytest_asyncio.fixture(autouse=True)
async def sem_rede(monkeypatch):
    """Impede qualquer chamada HTTP de provedor durante os testes.

    `criar_canal` chama `_configurar_webhook`, que fala com Telegram/WhatsApp/
    Meta/Discord. Em teste isso seria rede real com timeout de 10s por caso.
    """
    async def _fake(self, canal):
        return True

    monkeypatch.setattr(CanalService, "_configurar_webhook", _fake)


#: O schema valida o `identificador` por tipo: Telegram exige `ID:HASH`, os
#: demais exigem o número/id do canal. Um identificador genérico passaria no
#: Whatsapp e seria rejeitado no Telegram.
IDENTIFICADOR = {
    "whatsapp": "5511988880001",
    "telegram": "123456789:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw",
    "instagram": "17841400012345678",
    "facebook": "17841400012345678",
    "discord": "1234567890",
}


def _dto(telefone_id: int, tipo: str = "whatsapp", **kw) -> CanalContratadoCreate:
    return CanalContratadoCreate(
        tipo=tipo,
        telefone_id=telefone_id,
        identificador=IDENTIFICADOR.get(tipo, "5511988880001"),
        **kw,
    )


# ══════════════════════════════════════════════════════════════════════════════
# CRIAÇÃO
# ══════════════════════════════════════════════════════════════════════════════

class TestCriarCanal:
    async def test_cria_com_credenciais_e_token_de_webhook(
        self, db_session: AsyncSession, empresa: Empresa, telefone: Telefone
    ):
        service = CanalService(db_session)
        canal = await service.criar_canal(_dto(telefone.id, apelido="Zap Centro"), empresa.id)

        assert canal.id is not None
        assert canal.empresa_id == empresa.id
        assert canal.apelido == "Zap Centro"
        # `identificador` é dobrado dentro de `credenciais` pela chave do tipo.
        assert service._credenciais(canal)["phone_number"] == "5511988880001"
        # Sem token, qualquer um injetaria mensagem falsa na fila.
        assert canal.webhook_token

    async def test_token_informado_e_preservado(
        self, db_session: AsyncSession, empresa: Empresa, telefone: Telefone
    ):
        service = CanalService(db_session)
        canal = await service.criar_canal(
            _dto(telefone.id, webhook_token="token-fixo"), empresa.id
        )
        assert canal.webhook_token == "token-fixo"

    async def test_telefone_de_outra_empresa_e_recusado(
        self,
        db_session: AsyncSession,
        empresa: Empresa,
        telefone_outra_empresa: Telefone,
    ):
        """O telefone precisa ser do MESMO tenant.

        Sem esta validação, uma empresa contrataria canal sobre o número da
        outra e receberia as mensagens destined à concorrente.
        """
        service = CanalService(db_session)
        with pytest.raises(RecursoInvalidoError, match="não encontrado para esta empresa"):
            await service.criar_canal(_dto(telefone_outra_empresa.id), empresa.id)

    async def test_telefone_inativo_e_recusado(
        self, db_session: AsyncSession, empresa: Empresa, telefone_inativo: Telefone
    ):
        service = CanalService(db_session)
        with pytest.raises(RecursoInvalidoError, match="inativo"):
            await service.criar_canal(_dto(telefone_inativo.id), empresa.id)

    async def test_um_tipo_por_telefone(
        self, db_session: AsyncSession, empresa: Empresa, telefone: Telefone
    ):
        """Um WhatsApp por número; para um segundo, a empresa contrata outro número."""
        service = CanalService(db_session)
        await service.criar_canal(_dto(telefone.id, apelido="Primeiro"), empresa.id)
        with pytest.raises(CanalTipoInvalidoError, match="já possui um canal do tipo"):
            await service.criar_canal(_dto(telefone.id, apelido="Segundo"), empresa.id)

    async def test_outro_tipo_no_mesmo_telefone_e_permitido(
        self, db_session: AsyncSession, empresa: Empresa, telefone: Telefone
    ):
        service = CanalService(db_session)
        await service.criar_canal(_dto(telefone.id, tipo="whatsapp", apelido="Zap"), empresa.id)
        canal = await service.criar_canal(
            _dto(telefone.id, tipo="telegram", apelido="Telegram"), empresa.id
        )
        assert canal.tipo == "telegram"

    async def test_apelido_duplicado_na_mesma_empresa(
        self, db_session: AsyncSession, empresa: Empresa, telefone: Telefone
    ):
        service = CanalService(db_session)
        await service.criar_canal(_dto(telefone.id, apelido="Zap"), empresa.id)
        with pytest.raises(CanalNomeDuplicadoError, match="Já existe um canal"):
            await service.criar_canal(_dto(telefone.id, tipo="telegram", apelido="zap"), empresa.id)

    async def test_apelido_igu_em_outra_empresa_e_permitido(
        self,
        db_session: AsyncSession,
        empresa: Empresa,
        outra_empresa: Empresa,
        telefone: Telefone,
        telefone_outra_empresa: Telefone,
    ):
        service = CanalService(db_session)
        await service.criar_canal(_dto(telefone.id, apelido="Zap"), empresa.id)
        canal = await service.criar_canal(
            _dto(telefone_outra_empresa.id, apelido="Zap"), outra_empresa.id
        )
        assert canal.empresa_id == outra_empresa.id

    async def test_tipo_desconhecido_e_barrado_pelo_schema(
        self, db_session: AsyncSession, empresa: Empresa, telefone: Telefone
    ):
        """A primeira barreira é o `Literal` do tipo, antes do serviço."""
        with pytest.raises(ValidationError):
            _dto(telefone.id, tipo="carrier_pigeon")

    async def test_servico_rejeita_tipo_fora_da_lista(
        self, db_session: AsyncSession
    ):
        """Defesa em profundidade: `_validar_tipo_canal` aceita exatamente o
        mesmo conjunto do `Literal` do schema, então é inalcançável pela rota.
        Testado direto para não ficar sem cobertura."""
        service = CanalService(db_session)
        with pytest.raises(CanalTipoInvalidoError, match="não é suportado"):
            service._validar_tipo_canal("carrier_pigeon")

    @pytest.mark.parametrize("tipo", ["whatsapp", "telegram", "pabx", "email", "chat_web"])
    async def test_servico_aceita_tipos_validos(self, db_session: AsyncSession, tipo: str):
        CanalService(db_session)._validar_tipo_canal(tipo)


# ══════════════════════════════════════════════════════════════════════════════
# LEITURA E ISOLAMENTO
# ══════════════════════════════════════════════════════════════════════════════

class TestLeitura:
    async def test_busca_pela_propria_empresa(
        self, db_session: AsyncSession, empresa: Empresa, telefone: Telefone
    ):
        service = CanalService(db_session)
        canal = await service.criar_canal(_dto(telefone.id, apelido="Zap"), empresa.id)
        assert (await service.buscar_por_id(canal.id, empresa.id)).id == canal.id

    async def test_outra_empresa_nao_enxerga_o_canal(
        self,
        db_session: AsyncSession,
        empresa: Empresa,
        outra_empresa: Empresa,
        telefone: Telefone,
    ):
        """Isolamento por EMPRESA, não por Cliente.

        As duas empresas estão sob o mesmo `Cliente`, então um filtro por
        `cliente_id` deixaria uma ler a outra. Aqui a empresa B procura o canal
        da empresa A e não encontra.
        """
        service = CanalService(db_session)
        canal = await service.criar_canal(_dto(telefone.id, apelido="Zap"), empresa.id)
        with pytest.raises(CanalNaoEncontradoError):
            await service.buscar_por_id(canal.id, outra_empresa.id)

    async def test_listagem_respeita_tenant(
        self,
        db_session: AsyncSession,
        empresa: Empresa,
        outra_empresa: Empresa,
        telefone: Telefone,
        telefone_outra_empresa: Telefone,
    ):
        service = CanalService(db_session)
        await service.criar_canal(_dto(telefone.id, apelido="Canal A"), empresa.id)
        await service.criar_canal(_dto(telefone_outra_empresa.id, apelido="Canal B"), outra_empresa.id)

        canais, total = await service.listar_canais(empresa.id)
        assert total == 1
        assert [c.apelido for c in canais] == ["Canal A"]

    async def test_listagem_filtra_e_pagina(
        self, db_session: AsyncSession, empresa: Empresa, telefone: Telefone
    ):
        service = CanalService(db_session)
        await service.criar_canal(_dto(telefone.id, tipo="whatsapp", apelido="Zap"), empresa.id)
        await service.criar_canal(_dto(telefone.id, tipo="telegram", apelido="Telegram Oficial"), empresa.id)

        todos, total = await service.listar_canais(empresa.id)
        assert total == 2

        so_tg, total_tg = await service.listar_canais(empresa.id, tipo="telegram")
        assert total_tg == 1 and so_tg[0].apelido == "Telegram Oficial"

        so_ativos, total_ativos = await service.listar_canais(empresa.id, ativo=True)
        assert total_ativos == 2

        # Paginação: total continua reflecting o filtro, não a página.
        pagina, total_pag = await service.listar_canais(empresa.id, page=2, limit=1)
        assert len(pagina) == 1 and total_pag == 2

    async def test_listagem_vazia(self, db_session: AsyncSession, empresa: Empresa):
        service = CanalService(db_session)
        canais, total = await service.listar_canais(empresa.id)
        assert canais == [] and total == 0


# ══════════════════════════════════════════════════════════════════════════════
# ATUALIZAÇÃO
# ══════════════════════════════════════════════════════════════════════════════

class TestAtualizar:
    async def test_update_parcial(
        self, db_session: AsyncSession, empresa: Empresa, telefone: Telefone
    ):
        service = CanalService(db_session)
        canal = await service.criar_canal(_dto(telefone.id, apelido="Antigo"), empresa.id)
        await service.atualizar_canal(
            canal.id, empresa.id, CanalContratadoUpdate(apelido="Novo")
        )
        assert canal.apelido == "Novo"

    async def test_update_de_credenciais_nao_apaga_as_existentes(
        self, db_session: AsyncSession, empresa: Empresa, telefone: Telefone
    ):
        """Update parcial de credenciais precisa MESCLAR, não substituir.

        Se sobrescrevesse, o frontend que manda só o token novo apagaria o
        phone_number e o canal deixaria de saber qual número é.
        """
        service = CanalService(db_session)
        canal = await service.criar_canal(_dto(telefone.id, apelido="Zap"), empresa.id)
        await service.atualizar_canal(
            canal.id,
            empresa.id,
            CanalContratadoUpdate(credenciais={"access_token": "novo-token"}),
        )
        credenciais = service._credenciais(canal)
        assert credenciais["access_token"] == "novo-token"
        assert credenciais["phone_number"] == "5511988880001"

    async def test_update_vazio_nao_falha(
        self, db_session: AsyncSession, empresa: Empresa, telefone: Telefone
    ):
        service = CanalService(db_session)
        canal = await service.criar_canal(_dto(telefone.id, apelido="Zap"), empresa.id)
        assert (await service.atualizar_canal(canal.id, empresa.id, CanalContratadoUpdate())).id

    async def test_outra_empresa_nao_atualiza(
        self,
        db_session: AsyncSession,
        empresa: Empresa,
        outra_empresa: Empresa,
        telefone: Telefone,
    ):
        service = CanalService(db_session)
        canal = await service.criar_canal(_dto(telefone.id, apelido="Zap"), empresa.id)
        with pytest.raises(CanalNaoEncontradoError):
            await service.atualizar_canal(
                canal.id, outra_empresa.id, CanalContratadoUpdate(apelido="Sequestrado")
            )
        assert canal.apelido == "Zap"


# ══════════════════════════════════════════════════════════════════════════════
# SOFT DELETE
# ══════════════════════════════════════════════════════════════════════════════

class TestSoftDelete:
    async def test_delete_e_restore(
        self, db_session: AsyncSession, empresa: Empresa, telefone: Telefone
    ):
        service = CanalService(db_session)
        canal = await service.criar_canal(_dto(telefone.id, apelido="Zap"), empresa.id)

        assert await service.deletar_canal(canal.id, empresa.id) is True
        assert canal.deleted_at is not None
        assert canal.ativo is False
        # Soft delete some da listagem...
        with pytest.raises(CanalNaoEncontradoError):
            await service.buscar_por_id(canal.id, empresa.id)
        assert (await service.listar_canais(empresa.id))[1] == 0

        # ...mas o registro continua no banco: é a origem do histórico.
        restaurado = await service.restaurar_canal(canal.id, empresa.id)
        assert restaurado.deleted_at is None and restaurado.ativo is True

    async def test_delete_bloqueado_com_atendimento_em_aberto(
        self, db_session: AsyncSession, empresa: Empresa, telefone: Telefone, contato
    ):
        service = CanalService(db_session)
        canal = await service.criar_canal(_dto(telefone.id, apelido="Zap"), empresa.id)
        db_session.add(
            Atendimento(
                protocolo="ECO-1",
                status=StatusAtendimento.AGUARDANDO.value,
                canal_contratado_id=canal.id,
                contato_id=contato.id,
                empresa_id=empresa.id,
            )
        )
        await db_session.commit()

        with pytest.raises(RecursoInvalidoError, match="atendimento\\(s\\) em aberto"):
            await service.deletar_canal(canal.id, empresa.id)
        assert canal.deleted_at is None

    async def test_delete_permitido_com_atendimento_encerrado(
        self, db_session: AsyncSession, empresa: Empresa, telefone: Telefone, contato
    ):
        service = CanalService(db_session)
        canal = await service.criar_canal(_dto(telefone.id, apelido="Zap"), empresa.id)
        db_session.add(
            Atendimento(
                protocolo="ECO-2",
                status=StatusAtendimento.FINALIZADO.value,
                canal_contratado_id=canal.id,
                contato_id=contato.id,
                empresa_id=empresa.id,
            )
        )
        await db_session.commit()
        assert await service.deletar_canal(canal.id, empresa.id) is True

    async def test_outra_empresa_nao_deleta(
        self,
        db_session: AsyncSession,
        empresa: Empresa,
        outra_empresa: Empresa,
        telefone: Telefone,
    ):
        service = CanalService(db_session)
        canal = await service.criar_canal(_dto(telefone.id, apelido="Zap"), empresa.id)
        with pytest.raises(CanalNaoEncontradoError):
            await service.deletar_canal(canal.id, outra_empresa.id)
        assert canal.deleted_at is None


# ══════════════════════════════════════════════════════════════════════════════
# MÉTRICAS
# ══════════════════════════════════════════════════════════════════════════════

class TestMetricas:
    async def test_metricas_de_canal_inexistente_para_outra_empresa(
        self,
        db_session: AsyncSession,
        empresa: Empresa,
        outra_empresa: Empresa,
        telefone: Telefone,
    ):
        service = CanalService(db_session)
        canal = await service.criar_canal(_dto(telefone.id, apelido="Zap"), empresa.id)
        with pytest.raises(CanalNaoEncontradoError):
            await service.obter_metricas_canal(canal.id, outra_empresa.id)

    async def test_metricas_come_atendimentos_e_tempo_de_resposta(
        self, db_session: AsyncSession, empresa: Empresa, telefone: Telefone, contato
    ):
        agora = datetime.now(timezone.utc)
        service = CanalService(db_session)
        canal = await service.criar_canal(_dto(telefone.id, apelido="Zap"), empresa.id)

        db_session.add_all([
            Atendimento(
                protocolo="ECO-10", status=StatusAtendimento.AGUARDANDO.value,
                canal_contratado_id=canal.id, contato_id=contato.id,
                empresa_id=empresa.id, criado_em=agora,
            ),
            Atendimento(
                protocolo="ECO-11", status=StatusAtendimento.FINALIZADO.value,
                canal_contratado_id=canal.id, contato_id=contato.id,
                empresa_id=empresa.id, criado_em=agora,
                # resposta 2 min DEPOIS do inicio: o servico descarta pares
                # invertidos (r < i), entao um timestamp truncado zera a media.
                iniciado_em=agora, primeira_resposta_em=agora + timedelta(minutes=2),
            ),
        ])
        await db_session.commit()

        m = await service.obter_metricas_canal(canal.id, empresa.id)
        assert m["canal_id"] == canal.id
        assert m["tipo"] == "whatsapp"
        assert m["status"] == "ativo"
        assert m["atendimentos_hoje"] == 2
        assert m["atendimentos_ativos"] == 1
        assert m["tempo_medio_primeira_resposta_min"] == 2.0

    async def test_metricas_sem_atendimentos(
        self, db_session: AsyncSession, empresa: Empresa, telefone: Telefone
    ):
        service = CanalService(db_session)
        canal = await service.criar_canal(_dto(telefone.id, apelido="Zap"), empresa.id)
        m = await service.obter_metricas_canal(canal.id, empresa.id)
        assert m["atendimentos_hoje"] == 0
        assert m["atendimentos_ativos"] == 0
        assert m["tempo_medio_primeira_resposta_min"] is None

    async def test_contagem_por_tipo_ignora_excluidos_e_inativos(
        self,
        db_session: AsyncSession,
        empresa: Empresa,
        outra_empresa: Empresa,
        telefone: Telefone,
        telefone_outra_empresa: Telefone,
    ):
        service = CanalService(db_session)
        zap = await service.criar_canal(_dto(telefone.id, tipo="whatsapp", apelido="Zap"), empresa.id)
        await service.criar_canal(_dto(telefone.id, tipo="telegram", apelido="Telegram Oficial"), empresa.id)
        await service.criar_canal(
            _dto(telefone_outra_empresa.id, apelido="Outro tenant"), outra_empresa.id
        )
        await service.deletar_canal(zap.id, empresa.id)

        contagem = await service.contar_canais_por_tipo(empresa.id)
        assert contagem == {"telegram": 1}
