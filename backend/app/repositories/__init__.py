"""
Camada de repositórios.

Centraliza o acesso a dados (queries SQLAlchemy) isoladas por tenant (cliente_id),
permitindo que os serviços foquem em regras de negócio. O padrão segue o modelo
real do projeto (SQLAlchemy 2.0 / session direta), sem depender de DI global.
"""
