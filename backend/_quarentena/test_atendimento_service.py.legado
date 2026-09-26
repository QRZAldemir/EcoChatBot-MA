# tests/test_atendimento_service.py
"""
Testes unitários do AtendimentoService.
Valida a lógica de negócio, exceções de domínio e isolamento multi-tenant.
"""
import pytest
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.services.atendimento_service import AtendimentoService
from app.schemas.atendimento import (
    AtendimentoCreate, AtendimentoUpdate, AtendimentoTransferir,
    AtendimentoFinalizar, FiltroAtendimento
)
from app.models import Atendimento, Departamento
from app.exceptions import (
    AtendimentoNaoEncontradoError,
    AtendimentoFinalizadoError,
    RecursoInvalidoError
)


# ==============================================================================
# TESTES DE CRIAÇÃO
# ==============================================================================

class TestCriarAtendimento:
    """Testes para o método criar()."""
    
    def test_criar_atendimento_sucesso(
        self,
        service: AtendimentoService,
        departamento_triagem: Departamento
    ):
        """Deve criar um atendimento com sucesso e gerar protocolo único."""
        data = AtendimentoCreate(
            paciente_telefone="5511999999999",
            paciente_nome="Paciente Teste",
            tipo_canal=1,
            canal_id=1,
            departamento_id=departamento_triagem.id
        )
        
        resultado = service.criar(data)
        
        assert resultado.id is not None
        assert resultado.protocolo.startswith("ECO-")
        assert resultado.telefone == "5511999999999"
        assert resultado.nome_contato == "Paciente Teste"
        assert resultado.status == "aberto"
        assert resultado.departamento_id == departamento_triagem.id
        assert resultado.ativo is True
    
    def test_criar_atendimento_departamento_inexistente(self, service: AtendimentoService):
        """Deve lançar RecursoInvalidoError ao tentar criar com departamento inexistente."""
        data = AtendimentoCreate(
            paciente_telefone="5511999999999",
            paciente_nome="Paciente Teste",
            tipo_canal=1,
            canal_id=1,
            departamento_id=9999  # Inexistente
        )
        
        with pytest.raises(RecursoInvalidoError) as exc_info:
            service.criar(data)
        
        assert "Departamento" in str(exc_info.value)


# ==============================================================================
# TESTES DE BUSCA
# ==============================================================================

class TestBuscarAtendimento:
    """Testes para o método buscar_por_id()."""
    
    def test_buscar_por_id_sucesso(
        self,
        service: AtendimentoService,
        atendimento_aberto: Atendimento
    ):
        """Deve retornar o atendimento quando encontrado."""
        resultado = service.buscar_por_id(atendimento_aberto.id)
        
        assert resultado.id == atendimento_aberto.id
        assert resultado.protocolo == atendimento_aberto.protocolo
    
    def test_buscar_por_id_nao_encontrado(self, service: AtendimentoService):
        """Deve lançar AtendimentoNaoEncontradoError quando o ID não existe."""
        with pytest.raises(AtendimentoNaoEncontradoError) as exc_info:
            service.buscar_por_id(99999)
        
        assert "não encontrado" in str(exc_info.value).lower()
    
    def test_buscar_por_id_isolamento_multi_tenant(
        self,
        db_session: Session,
        service: AtendimentoService,
        departamento_triagem: Departamento,
        departamento_suporte: Departamento,
        usuario_atendente: Usuario
    ):
        """
        Deve lançar AtendimentoNaoEncontradoError quando o usuário tenta acessar
        um atendimento de outro departamento (isolamento multi-tenant).
        """
        # Cria atendimento no departamento de Suporte
        atendimento_outro_depto = Atendimento(
            protocolo="ECO-OUTRO-001",
            telefone="5511555555555",
            nome_contato="Paciente Outro Depto",
            tipo_canal=1,
            canal_id=1,
            departamento_id=departamento_suporte.id,  # Departamento diferente
            status="aberto",
            ativo=True,
            criado_em=datetime.now(timezone.utc)
        )
        db_session.add(atendimento_outro_depto)
        db_session.commit()
        
        # Tenta buscar com usuario_id do departamento de Triagem
        # usuario_atendente pertence a departamento_triagem, não departamento_suporte
        with pytest.raises(AtendimentoNaoEncontradoError):
            service.buscar_por_id(
                atendimento_outro_depto.id,
                usuario_id=usuario_atendente.id
            )


# ==============================================================================
# TESTES DE ATUALIZAÇÃO
# ==============================================================================

class TestAtualizarAtendimento:
    """Testes para o método atualizar()."""
    
    def test_atualizar_atendimento_sucesso(
        self,
        service: AtendimentoService,
        atendimento_aberto: Atendimento
    ):
        """Deve atualizar os campos permitidos do atendimento."""
        data = AtendimentoUpdate(
            status="fila",
            nome_contato="Nome Atualizado"
        )
        
        resultado = service.atualizar(atendimento_aberto.id, data)
        
        assert resultado.status == "fila"
        assert resultado.nome_contato == "Nome Atualizado"
        assert resultado.atualizado_em is not None
    
    def test_atualizar_atendimento_finalizado_falha(
        self,
        service: AtendimentoService,
        atendimento_finalizado: Atendimento
    ):
        """Deve lançar AtendimentoFinalizadoError ao tentar atualizar atendimento finalizado."""
        data = AtendimentoUpdate(status="aberto")
        
        with pytest.raises(AtendimentoFinalizadoError):
            service.atualizar(atendimento_finalizado.id, data)


# ==============================================================================
# TESTES DE TRANSFERÊNCIA
# ==============================================================================

class TestTransferirAtendimento:
    """Testes para o método transferir()."""
    
    def test_transferir_para_departamento_sucesso(
        self,
        service: AtendimentoService,
        atendimento_aberto: Atendimento,
        departamento_suporte: Departamento,
        usuario_atendente: Usuario
    ):
        """Deve transferir atendimento para outro departamento com sucesso."""
        data = AtendimentoTransferir(
            departamento_id=departamento_suporte.id
        )
        
        resultado = service.transferir(
            atendimento_aberto.id,
            data,
            usuario_id=usuario_atendente.id
        )
        
        assert resultado.departamento_id == departamento_suporte.id
        assert resultado.status == "fila"  # Sem usuário atribuído
    
    def test_transferir_para_usuario_sucesso(
        self,
        service: AtendimentoService,
        atendimento_aberto: Atendimento,
        usuario_atendente: Usuario
    ):
        """Deve transferir atendimento para um usuário específico."""
        data = AtendimentoTransferir(
            usuario_id=usuario_atendente.id
        )
        
        resultado = service.transferir(
            atendimento_aberto.id,
            data,
            usuario_id=usuario_atendente.id
        )
        
        assert resultado.usuario_id == usuario_atendente.id
        assert resultado.status == "em_atendimento"  # Com usuário atribuído
    
    def test_transferir_atendimento_finalizado_falha(
        self,
        service: AtendimentoService,
        atendimento_finalizado: Atendimento,
        departamento_suporte: Departamento,
        usuario_atendente: Usuario
    ):
        """Deve lançar AtendimentoFinalizadoError ao tentar transferir atendimento finalizado."""
        data = AtendimentoTransferir(departamento_id=departamento_suporte.id)
        
        with pytest.raises(AtendimentoFinalizadoError):
            service.transferir(
                atendimento_finalizado.id,
                data,
                usuario_id=usuario_atendente.id
            )
    
    def test_transferir_departamento_inexistente_falha(
        self,
        service: AtendimentoService,
        atendimento_aberto: Atendimento,
        usuario_atendente: Usuario
    ):
        """Deve lançar RecursoInvalidoError ao transferir para departamento inexistente."""
        data = AtendimentoTransferir(departamento_id=9999)
        
        with pytest.raises(RecursoInvalidoError):
            service.transferir(
                atendimento_aberto.id,
                data,
                usuario_id=usuario_atendente.id
            )


# ==============================================================================
# TESTES DE FINALIZAÇÃO
# ==============================================================================

class TestFinalizarAtendimento:
    """Testes para o método finalizar()."""
    
    def test_finalizar_atendimento_sucesso(
        self,
        service: AtendimentoService,
        atendimento_em_atendimento: Atendimento
    ):
        """Deve finalizar um atendimento com sucesso."""
        resultado = service.finalizar(atendimento_em_atendimento.id)
        
        assert resultado.status == "finalizado"
        assert resultado.atualizado_em is not None
    
    def test_finalizar_atendimento_ja_finalizado_falha(
        self,
        service: AtendimentoService,
        atendimento_finalizado: Atendimento
    ):
        """Deve lançar AtendimentoFinalizadoError ao tentar finalizar atendimento já finalizado."""
        with pytest.raises(AtendimentoFinalizadoError):
            service.finalizar(atendimento_finalizado.id)


# ==============================================================================
# TESTES DE LISTAGEM
# ==============================================================================

class TestListarAtendimentos:
    """Testes para o método listar()."""
    
    def test_listar_sem_filtros(
        self,
        service: AtendimentoService,
        atendimento_aberto: Atendimento,
        atendimento_em_fila: Atendimento
    ):
        """Deve listar todos os atendimentos ativos quando nenhum filtro é aplicado."""
        resultado = service.listar()
        
        assert resultado["total"] >= 2
        assert len(resultado["registros"]) >= 2
        assert resultado["pagina"] == 1
        assert resultado["limit"] == 50
    
    def test_listar_com_filtro_status(
        self,
        service: AtendimentoService,
        atendimento_aberto: Atendimento,
        atendimento_em_fila: Atendimento,
        atendimento_finalizado: Atendimento
    ):
        """Deve filtrar atendimentos por status."""
        filtros = FiltroAtendimento(status="aberto")
        resultado = service.listar(filtros=filtros)
        
        assert all(a.status == "aberto" for a in resultado["registros"])
    
    def test_listar_com_paginacao(
        self,
        service: AtendimentoService,
        atendimento_aberto: Atendimento,
        atendimento_em_fila: Atendimento
    ):
        """Deve aplicar paginação corretamente."""
        resultado = service.listar(page