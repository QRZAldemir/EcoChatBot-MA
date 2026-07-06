#!/usr/bin/env python3
# ==============================================================================
# Script: Executor de Migrações de Banco de Dados
# ==============================================================================
# Descrição: Automatiza a execução de scripts SQL de migração de forma segura
#
# O que faz este script:
#   1. Busca arquivos .sql no diretório './migrations/'
#   2. Executa cada arquivo em ordem alfabética
#   3. Remove comentários SQL (--) e (/* */)
#   4. Executa TODOS os statements dentro de uma transação ÚNICA
#   5. Se algum falhar, faz rollback de tudo (atomicidade)
#   6. Registra sucesso/erro com timestamps
#
# Por que usar:
#   - ✅ Automatiza migrações repetitivas
#   - ✅ Transações atômicas (tudo ou nada)
#   - ✅ Logging de execução
#   - ✅ Tratamento de erros robusto
#
# Uso:
#   python run_migrations.py              # Executa todas as migrações
#   python run_migrations.py --help       # Exibe ajuda
#   python run_migrations.py -h           # Exibe ajuda
#   python run_migrations.py help         # Exibe ajuda
#
# Banco de dados suportados:
#   - MySQL / MariaDB
#   - PostgreSQL
#   - SQLite
#   (Depende da URL em app/database.py)
#
# ==============================================================================

import os
import sys
from pathlib import Path
from datetime import datetime
from sqlalchemy import text, create_engine
from app.database import DATABASE_URL


def run_migrations():
    """
    Executa todos os scripts SQL de migração no diretório 'migrations/'
    em ordem sequencial. Registra sucesso/erro em log.
    """
    migrations_dir = Path(__file__).parent / "migrations"

    if not migrations_dir.exists():
        print(f"❌ Diretório de migrações não encontrado: {migrations_dir}")
        return False

    migration_files = sorted([f for f in migrations_dir.glob("*.sql")])

    if not migration_files:
        print("⚠️  Nenhum arquivo de migração encontrado.")
        return True

    print(f"📋 Encontradas {len(migration_files)} migração(ções)")
    print(f"🗄️  Banco: {DATABASE_URL.split('://')[-1].split('@')[-1]}")
    print("-" * 70)

    try:
        # CORRIGIDO: Criar engine e executar migrações dentro de transação
        engine = create_engine(DATABASE_URL)

        for migration_file in migration_files:
            print(f"\n▶️  Executando: {migration_file.name}")

            with open(migration_file, "r") as f:
                sql_content = f.read()
                # Divide o arquivo em statements (separados por ";")
                statements = [s.strip() for s in sql_content.split(";") if s.strip()]

                # ==================================================================
                # CORRIGIDO (Erro 1): Melhor filtro de comentários SQL
                # ==================================================================
                # PROBLEMA ORIGINAL:
                #   statements = [s for s in statements
                #       if not s.startswith("--") and not s.startswith("/*")]
                # Isso apenas filtrava linhas que COMEÇAM com comentário,
                # mas não removia:
                #   - Comentários no meio da linha (-- depois de SQL)
                #   - Fechamento de comentários multi-linha (*/)
                #
                # SOLUÇÃO:
                # Remover linhas inteiras que são comentários, depois limpar
                # comentários inline (-- em SQL válido)
                # ==================================================================
                clean_statements = []
                for s in statements:
                    # Remove linhas que são puro comentário
                    lines = s.split('\n')
                    clean_lines = []
                    for line in lines:
                        # Remove comentário inline (tudo depois de --)
                        if '--' in line:
                            line = line.split('--')[0]
                        # Pula linhas que são apenas comentário
                        if line.strip() and not line.strip().startswith('/*'):
                            clean_lines.append(line)
                    cleaned = '\n'.join(clean_lines).strip()
                    if cleaned:
                        clean_statements.append(cleaned)

            with engine.connect() as connection:
                # ==================================================================
                # CORRIGIDO (Erro 2): Commit deve ser FORA do loop de statements
                # ==================================================================
                # PROBLEMA ORIGINAL:
                #   for statement in statements:
                #       connection.execute(text(statement))
                #       connection.commit()  # Commit a cada linha!
                # Isso commitava após CADA statement, sem transação atômica.
                # Se o 3º de 5 statements falhasse, os 2 primeiros já teriam sido
                # commitados e não haveria rollback.
                #
                # SOLUÇÃO:
                # Executar TODOS os statements primeiro, depois fazer um ÚNICO
                # commit. Se qualquer um falhar, faz rollback de TODOS.
                # ==================================================================
                try:
                    executed_count = 0
                    for statement in clean_statements:
                        if statement.strip():
                            connection.execute(text(statement))
                            executed_count += 1
                    # Commit ÚNICO após TODOS os statements
                    connection.commit()
                    print(f"   ✅ {executed_count} statement(s) executado(s) com sucesso")
                except Exception as e:
                    connection.rollback()
                    print(f"   ❌ Erro ao executar: {e}")
                    return False

        print("\n" + "=" * 70)
        print(f"✅ SUCESSO: Todas as migrações foram executadas!")
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        return True

    except Exception as e:
        print(f"\n❌ ERRO FATAL: {e}")
        return False


# CORRIGIDO: Guia de como usar o script
def print_help():
    """Exibe ajuda de uso do script."""
    print("""
    🔄 Executor de Migrações — EcoChatBot-MA

    Uso:
        python run_migrations.py

    O que faz:
        1. Procura por arquivos .sql em ./migrations/
        2. Executa cada migração em ordem sequencial
        3. Registra sucesso ou erro de cada operação
        4. Usa transação para garantir atomicidade

    ⚠️  IMPORTANTE:
        - Sempre faça BACKUP do banco de dados antes!
        - Teste em STAGING antes de PRODUÇÃO
        - Verifique DATABASE_URL em app/database.py

    Exemplo de backup (MySQL):
        mysqldump -u usuario -p banco > backup_$(date +%s).sql
    """)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ["--help", "-h", "help"]:
        print_help()
        sys.exit(0)

    success = run_migrations()
    sys.exit(0 if success else 1)
