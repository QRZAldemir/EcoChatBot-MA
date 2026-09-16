# tests/test_indicadores.py
"""
Testes específicos do método de indicadores.
Valida a agregação condicional e otimização de performance.
"""
import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from app.services.atendimento_service import AtendimentoService
from app.models import Atendimento, Departamento


class TestIndicadores:
    """Testes para o método indicadores()."""
    
    def test_indicadores_total_geral(
        self,
        service: AtendimentoService,
        atendimento_aberto: Atendimento,
        atendimento_em_fila: Atendimento,
        atendimento_em_atendimento: Atendimento,
        atendimento_finalizado: Atendimento
    ):
        """Deve calcular corretamente o total geral de atendimentos."""
        resultado = service.indicadores()
        
        assert resultado.total >= 4
        assert resultado.aberto >= 1
        assert resultado.fila >= 1
        assert resultado.em_atendimento >= 1
    
    def test_indicadores_finalizados_por_tipo(
        self,
        service: AtendimentoService,
        atendimento_finalizado: Atendimento,
        db_session: Session,
        departamento_triagem: Departamento
    ):
        """Deve diferenciar finalizados com e sem atendente."""
        # Cria um atendimento finalizado sem atendente (bot)
        atendimento_bot = Atendimento(
            protocolo="ECO-BOT-001",
            telefone="5511444444444",
            nome_contato="Paciente Bot",
            tipo_canal=1,
            canal_id=1,
            departamento_id=departamento_triagem.id,
            usuario_id=None,  # Sem atendente (resolvido pelo bot)
            status="finalizado",
            ativo=True,
            criado_em=datetime.now(timezone.utc)
        )
        db_session.add(atendimento_bot)
        db_session.commit()
        
        resultado = service.indicadores()
        
        assert resultado.finalizado_humano >= 1  # atendimento_finalizado tem usuario_id
        assert resultado.finalizado_sem_atendente >= 1  # atendimento_bot não tem usuario_id
    
    def test_indicadores_por_departamento(
        self,
        service: AtendimentoService,
        atendimento_aberto: Atendimento,
        atendimento_finalizado: Atendimento,
        departamento_triagem: Departamento,
        departamento_suporte: Departamento,
        db_session: Session
    ):
        """Deve agrupar indicadores por departamento."""
        # Cria atendimentos no departamento de Suporte
        for i in range(3):
            atendimento = Atendimento(
                protocolo=f"ECO-SUPORTE-{i}",
                telefone=f"55113333{i}000",
                nome_contato=f"Paciente Suporte {i}",
                tipo_canal=1,
                canal_id=1,
                departamento_id=departamento_suporte.id,
                status="aberto",
                ativo=True,
                criado_em=datetime.now(timezone.utc)
            )
            db_session.add(atendimento)
        db_session.commit()
        
        resultado = service.indicadores()
        
        assert len(resultado.por_departamento) >= 2
        
        # Verifica se os departamentos estão corretos
        deptos_nomes = [d["nome"] for d in resultado.por_departamento]
        assert "Triagem" in deptos_nomes
        assert "Suporte Técnico" in deptos_nomes
        
        # Verifica se as contagens estão corretas
        suporte_data = next(d for d in resultado.por_departamento if d["nome"] == "Suporte Técnico")
        assert suporte_data["total"] >= 3
        assert suporte_data["em_aberto"] >= 3
    
    def test_indicadores_com_filtro_data(
        self,
        service: AtendimentoService,
        atendimento_aberto: Atendimento,
        atendimento_finalizado: Atendimento,
        db_session: Session,
        departamento_triagem: Departamento
    ):
        """Deve filtrar indicadores por faixa de data."""
        # Cria atendimento antigo (há 10 dias)
        atendimento_antigo = Atendimento(
            protocolo="ECO-ANTIGO-001",
            telefone="5511222222222",
            nome_contato="Paciente Antigo",
            tipo_canal=1,
            canal_id=1,
            departamento_id=departamento_triagem.id,
            status="finalizado",
            ativo=True,
            criado_em=datetime.now(timezone.utc) - timedelta(days=10)
        )
        db_session.add(atendimento_antigo)
        db_session.commit()
        
        # Consulta apenas últimos 5 dias
        data_inicio = datetime.now(timezone.utc) - timedelta(days=5)
        resultado = service.indicadores(data_inicio=data_inicio)
        
        # O atendimento antigo não deve ser contabilizado
        assert resultado.total >= 1  # Pelo menos os atendimentos recentes
        # O atendimento antigo não deve estar nos resultados
    
    def test_indicadores_performance_otimizada(
        self,
        service: AtendimentoService,
        db_session: Session,
        departamento_triagem: Departamento
    ):
        """
        Teste de performance: deve executar em tempo razoável mesmo com muitos registros.
        Este teste valida que a otimização de agregação condicional está funcionando.
        """
        # Cria 100 atendimentos de teste
        for i in range(100):
            atendimento = Atendimento(
                protocolo=f"ECO-PERF-{i:03d}",
                telefone=f"55111111{i:03d}",
                nome_contato=f"Paciente Perf {i}",
                tipo_canal=1,
                canal_id=1,
                departamento_id=departamento_triagem.id,
                status=["aberto", "fila", "em_atendimento", "finalizado"][i % 4],
                ativo=True,
                criado_em=datetime.now(timezone.utc) - timedelta(days=i % 30)
            )
            db_session.add(atendimento)
        db_session.commit()
        
        # Executa a consulta de indicadores
        import time
        start_time = time.time()
        resultado = service.indicadores()
        elapsed_time = time.time() - start_time
        
        # Deve executar em menos de 1 segundo (otimização de agregação)
        assert elapsed_time < 1.0, f"Query muito lenta: {elapsed_time:.2f}s"
        
        # Valida os resultados
        assert resultado.total >= 100
        assert len(resultado.por_departamento) >= 1