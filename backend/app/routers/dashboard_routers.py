"""
================================================================================
MÓDULO: app/routers/dashboard.py
AUTOR: Aldemir Queiroz da Silva
VERSÃO: 2.0.0 (Integração e Segurança)
OBJETIVO: Router de métricas e KPIs para o Dashboard Administrativo.
          Utiliza a Engine de Leitura (Replica) para não impactar as escritas.
================================================================================
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, date
from typing import Optional

# Importações do projeto
from app.database import get_db_read
from app.security import exigir_nivel_minimo
from app.models import Atendimento, Usuario, Canal # Ajuste conforme seus models reais

router = APIRouter()

# ==============================================================================
# ENDPOINTS DE DASHBOARD (Protegidos - Nível Gerente ou Superior)
# ==============================================================================

@router.get("/kpis", response_model=dict)
def get_kpis(
    data_inicial: Optional[date] = Query(None),
    data_final: Optional[date] = Query(None),
    departamento_id: Optional[int] = Query(None),
    db: Session = Depends(get_db_read),
    _ = Depends(exigir_nivel_minimo("gerente")) # Exige autenticação e nível gerente
):
    """
    Retorna os KPIs principais do dashboard.
    Utiliza a sessão de leitura (Replica) para otimizar performance.
    """
    # Filtros base
    filtros = []
    if data_inicial and data_final:
        filtros.append(and_(Atendimento.criado_em >= data_inicial, Atendimento.criado_em <= data_final))
    if departamento_id:
        filtros.append(Atendimento.departamento_id == departamento_id)

    # Consultas reais ao banco (Exemplo com SQLAlchemy)
    total_periodo = db.query(func.count(Atendimento.id)).filter(*filtros).scalar() or 0
    total_abertos = db.query(func.count(Atendimento.id)).filter(Atendimento.status == 'aberto', *filtros).scalar() or 0
    total_finalizados = db.query(func.count(Atendimento.id)).filter(Atendimento.status == 'finalizado', *filtros).scalar() or 0
    
    # Em produção, calcule as médias via SQL nativo ou agregações do SQLAlchemy
    return {
        "atendimentos_periodo": total_periodo,
        "atendimentos_abertos": total_abertos,
        "atendimentos_finalizados": total_finalizados,
        "atendimentos_automaticos": 0, # Implementar lógica de filtro por tipo
        "atendimentos_manuais": 0,     # Implementar lógica de filtro por tipo
        "tempo_medio_atendimento": "0h", # Calcular via AVG no SQL
        "tempo_medio_espera": "0m",      # Calcular via AVG no SQL
        "aguardando_atendimento": 0,
        "aguardando_resposta": 0
    }


@router.get("/grafico/insight", response_model=dict)
def get_insight_mensagens(
    mes: int = Query(..., ge=1, le=12),
    ano: int = Query(..., ge=2024, le=2030),
    db: Session = Depends(get_db_read),
    _ = Depends(exigir_nivel_minimo("gerente"))
):
    """
    Retorna os dados para o gráfico de barras (Insight de Mensagens por Canal).
    """
    # Exemplo de query agrupando por canal
    resultados = db.query(
        Canal.nome, 
        func.count(Atendimento.id).label('total')
    ).join(Atendimento, Atendimento.canal_id == Canal.id).filter(
        func.extract('month', Atendimento.criado_em) == mes,
        func.extract('year', Atendimento.criado_em) == ano
    ).group_by(Canal.nome).all()

    labels = [r.nome for r in resultados]
    data = [r.total for r in resultados]
    max_value = max(data) if data else 0

    return {
        "labels": labels,
        "data": data,
        "max_value": max_value if max_value > 0 else 1 # Evita divisão por zero no frontend
    }


@router.get("/atendentes", response_model=dict)
def get_atendentes(
    db: Session = Depends(get_db_read),
    _ = Depends(exigir_nivel_minimo("gerente"))
):
    """
    Retorna a lista de atendentes e seus status de conexão.
    """
    atendentes = db.query(Usuario).filter(Usuario.ativo == True).all()
    
    online = [{"id": u.id, "nome": u.nome, "status": "online"} for u in atendentes if u.status_conexao == 'online']
    offline = [{"id": u.id, "nome": u.nome, "status": "offline"} for u in atendentes if u.status_conexao != 'online']

    return {
        "online": online,
        "offline": offline,
        "total_online": len(online),
        "total_offline": len(offline),
        "total_geral": len(atendentes)
    }