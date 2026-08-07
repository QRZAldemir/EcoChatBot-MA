"""
================================================================================
SCRIPT DE EXPORTAÇÃO DO SCHEMA OPENAPI (CONTRATO API PYTHON -> ANGULAR)
================================================================================
Autor: Aldemir Queiroz da Silva
Versão: 1.0.0
Data de Criação: 07 de Agosto de 2026
================================================================================
FINALIDADE DO SCRIPT:
O FastAPI já gera automaticamente a documentação interativa (Swagger UI em
/docs e ReDoc em /redoc) a partir dos routers e dos schemas Pydantic - isso
substitui, no mundo Python, o papel que bibliotecas como springdoc-openapi
(Spring Boot) ou SmallRye OpenAPI (Quarkus) cumprem no mundo Java.

Este script fecha a outra ponta da integração: ele importa a instância `app`
sem precisar subir o servidor (nem depender de conexão ativa com o banco,
já que a Engine do SQLAlchemy só conecta de fato na primeira query) e grava
o schema OpenAPI resultante em `openapi.json`, na raiz do backend.

Esse arquivo é consumido pelo `openapi-typescript-codegen` no frontend
(ver script "generate:api" em frontend/package.json) para gerar
automaticamente os services e models Angular a partir do contrato real da
API - garantindo que a "interface de teste" do frontend nunca fique
dessincronizada da versão atual da aplicação.

USO:
    python export_openapi.py
================================================================================
"""

import json
from pathlib import Path

from app.main import app

OUTPUT_PATH = Path(__file__).parent / "openapi.json"


def exportar_schema() -> None:
    """Gera o schema OpenAPI da aplicação e grava em openapi.json."""
    schema = app.openapi()
    OUTPUT_PATH.write_text(
        json.dumps(schema, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Schema OpenAPI exportado para: {OUTPUT_PATH}")
    print(f"Endpoints encontrados: {len(schema.get('paths', {}))}")


if __name__ == "__main__":
    exportar_schema()
