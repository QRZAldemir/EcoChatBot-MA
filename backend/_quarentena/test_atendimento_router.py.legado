# tests/test_atendimento_router.py
"""
Testes de integração do Router de Atendimento.
Valida os endpoints REST, validação de entrada e formato de resposta ZigResponse.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Atendimento, Departamento


# ==============================================================================
# TESTES DO ENDPOINT /listar
# ==============================================================================

class TestListarEndpoint:
    """Testes para o endpoint GET /atendimento/listar."""
    
    def test_listar_sucesso(
        self,
        client: TestClient,
        atendimento_aberto: Atendimento
    ):
        """Deve retornar lista de atendimentos com formato ZigResponse."""
        response = client.get("/atendimento/listar")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["codigo"] == 0
        assert "dados" in data
        assert "total" in data["dados"]
        assert "registros" in data["dados"]
        assert data["dados"]["total"] >= 1
    
    def test_listar_com_filtros(
        self,
        client: TestClient,
        atendimento_aberto: Atendimento
    ):
        """Deve aplicar filtros via query parameters."""
        response = client.get("/atendimento/listar?status=aberto&limit=10")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["codigo"] == 0
        assert data["dados"]["limit"] == 10
    
    def test_listar_paginacao_invalida(
        self,
        client: TestClient
    ):
        """Deve retornar erro de validação para paginação inválida."""
        response = client.get("/atendimento/listar?page=0")
        
        assert response.status_code == 422  # Unprocessable Entity


# ==============================================================================
# TESTES DO ENDPOINT /transferir
# ==============================================================================

class TestTransferirEndpoint:
    """Testes para o endpoint POST /atendimento/transferir."""
    
    def test_transferir_sucesso(
        self,
        client: TestClient,
        atendimento_aberto: Atendimento,
        departamento_suporte: Departamento
    ):
        """Deve transferir atendimento com sucesso."""
        payload = {
            "atendimento_id": atendimento_aberto.id,
            "departamento_id": departamento_suporte.id
        }
        
        response = client.post("/atendimento/transferir", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["codigo"] == 0
        assert data["dados"]["atendimento_id"] == atendimento_aberto.id
        assert data["dados"]["departamento_id"] == departamento_suporte.id
    
    def test_transferir_sem_destino_falha(
        self,
        client: TestClient,
        atendimento_aberto: Atendimento
    ):
        """Deve retornar erro quando nenhum destino é especificado."""
        payload = {
            "atendimento_id": atendimento_aberto.id
            # Sem departamento_id, usuario_id ou canal_id
        }
        
        response = client.post("/atendimento/transferir", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["codigo"] == 1
        assert "departamento_id" in data["erro"].lower() or "atendente" in data["erro"].lower()
    
    def test_transferir_atendimento_inexistente(
        self,
        client: TestClient,
        departamento_suporte: Departamento
    ):
        """Deve retornar erro para atendimento inexistente."""
        payload = {
            "atendimento_id": 99999,
            "departamento_id": departamento_suporte.id
        }
        
        response = client.post("/atendimento/transferir", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["codigo"] == 1
        assert "não encontrado" in data["erro"].lower()


# ==============================================================================
# TESTES DO ENDPOINT /encerrar
# ==============================================================================

class TestEncerrarEndpoint:
    """Testes para o endpoint POST /atendimento/encerrar."""
    
    def test_encerrar_sucesso(
        self,
        client: TestClient,
        atendimento_em_atendimento: Atendimento
    ):
        """Deve encerrar atendimento com sucesso."""
        payload = {
            "atendimento_id": atendimento_em_atendimento.id
        }
        
        response = client.post("/atendimento/encerrar", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["codigo"] == 0
        assert data["dados"]["status"] == "finalizado"
    
    def test_encerrar_atendimento_inexistente(self, client: TestClient):
        """Deve retornar erro para atendimento inexistente."""
        payload = {
            "atendimento_id": 99999
        }
        
        response = client.post("/atendimento/encerrar", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["codigo"] == 1
        assert "não encontrado" in data["erro"].lower()
    
    def test_encerrar_atendimento_ja_finalizado(
        self,
        client: TestClient,
        atendimento_finalizado: Atendimento
    ):
        """Deve retornar erro ao tentar encerrar atendimento já finalizado."""
        payload = {
            "atendimento_id": atendimento_finalizado.id
        }
        
        response = client.post("/atendimento/encerrar", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["codigo"] == 1
        assert "finalizado" in data["erro"].lower()


# ==============================================================================
# TESTES DO ENDPOINT /context
# ==============================================================================

class TestContextEndpoint:
    """Testes para endpoints de contexto."""
    
    def test_consultar_context_nao_encontrado(
        self,
        client: TestClient,
        atendimento_aberto: Atendimento
    ):
        """Deve retornar erro quando contexto não existe."""
        response = client.get(
            f"/atendimento/context/{atendimento_aberto.id}/chave_inexistente"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["codigo"] == 1
        assert "não encontrado" in data["erro"].lower()