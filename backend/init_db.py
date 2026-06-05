from app.database import engine, Base
from app.models import NivelUsuario, Departamento, Canal, Usuario
from app.services.usuario_service import hash_senha
from sqlalchemy.orm import Session
from app.database import SessionLocal

def init_db():
    """Inicializar banco de dados com tabelas e dados básicos"""
    
    # Criar tabelas
    Base.metadata.create_all(bind=engine)
    
    # Criar sessão
    db = SessionLocal()
    
    try:
        # Verificar se já existem dados
        if db.query(NivelUsuario).count() > 0:
            print("Banco de dados já inicializado.")
            return
        
        print("Inicializando banco de dados...")
        
        # 1. Criar níveis de usuário
        niveis = [
            NivelUsuario(nome="atendente", descricao="Atendente de suporte"),
            NivelUsuario(nome="supervisor", descricao="Supervisor de equipe"),
            NivelUsuario(nome="gerente", descricao="Gerente de operações"),
            NivelUsuario(nome="administrador", descricao="Administrador do sistema")
        ]
        db.add_all(niveis)
        db.flush()
        
        # 2. Criar departamentos
        departamentos = [
            Departamento(nome="Call-Center", descricao="Central de atendimento telefônico"),
            Departamento(nome="Recepção", descricao="Recepção e portaria do hospital"),
            Departamento(nome="Ouvidoria", descricao="Ouvidoria e relações com pacientes"),
            Departamento(nome="Agendamento", descricao="Agendamento de consultas e exames"),
            Departamento(nome="Exames", descricao="Centro de diagnósticos e exames")
        ]
        db.add_all(departamentos)
        db.flush()
        
        # Mapear departamentos por nome para fácil acesso
        depto_map = {d.nome: d for d in departamentos}
        
        # 3. Criar canais
        canais = [
            Canal(
                nome="Atendimento-Cliente",
                descricao="Canal de atendimento geral ao cliente",
                arquivo_menu="1atendimento-mackenzie.html",
                departamento_id=depto_map["Call-Center"].id
            ),
            Canal(
                nome="Agendamento-Ambulatorial",
                descricao="Agendamento de consultas ambulatoriais",
                arquivo_menu="2agendamento-mackenzie.html",
                departamento_id=depto_map["Agendamento"].id
            ),
            Canal(
                nome="Exames-Diagnostico",
                descricao="Agendamento e resultados de exames",
                arquivo_menu="3examesdiagnostico-mackenzie.html",
                departamento_id=depto_map["Exames"].id
            ),
            Canal(
                nome="Portaria",
                descricao="Controle de acesso e informações da portaria",
                arquivo_menu="7portaria-mackenzie.html",
                departamento_id=depto_map["Recepção"].id
            ),
            Canal(
                nome="Ouvidoria",
                descricao="Canal de ouvidoria para reclamações e sugestões",
                arquivo_menu="8ouvidoria-mackenzie.html",
                departamento_id=depto_map["Ouvidoria"].id
            )
        ]
        db.add_all(canais)
        db.flush()
        
        # Mapear canais por nome
        canal_map = {c.nome: c for c in canais}
        
        # 4. Criar usuários de exemplo
        usuarios = [
            Usuario(
                nome="Ana Silva",
                email="ana@hospitalmackenzie.com.br",
                senha_hash=hash_senha("senha123"),
                telefone="(67) 99999-1111",
                nivel_id=niveis[0].id,  # atendente
                departamento_id=depto_map["Call-Center"].id,
                canal_id=canal_map["Atendimento-Cliente"].id
            ),
            Usuario(
                nome="João Santos",
                email="joao@hospitalmackenzie.com.br",
                senha_hash=hash_senha("senha123"),
                telefone="(67) 99999-2222",
                nivel_id=niveis[0].id,  # atendente
                departamento_id=depto_map["Recepção"].id,
                canal_id=canal_map["Portaria"].id
            ),
            Usuario(
                nome="Francisca Oliveira",
                email="francisca@hospitalmackenzie.com.br",
                senha_hash=hash_senha("senha123"),
                telefone="(67) 99999-3333",
                nivel_id=niveis[0].id,  # atendente
                departamento_id=depto_map["Ouvidoria"].id,
                canal_id=canal_map["Ouvidoria"].id
            ),
            Usuario(
                nome="Daniele Costa",
                email="daniele@hospitalmackenzie.com.br",
                senha_hash=hash_senha("senha123"),
                telefone="(67) 99999-4444",
                nivel_id=niveis[0].id,  # atendente
                departamento_id=depto_map["Agendamento"].id,
                canal_id=canal_map["Agendamento-Ambulatorial"].id
            ),
            Usuario(
                nome="Aldemir Pereira",
                email="aldemir@hospitalmackenzie.com.br",
                senha_hash=hash_senha("senha123"),
                telefone="(67) 99999-5555",
                nivel_id=niveis[0].id,  # atendente
                departamento_id=depto_map["Exames"].id,
                canal_id=canal_map["Exames-Diagnostico"].id
            ),
            Usuario(
                nome="Carlos Admin",
                email="admin@hospitalmackenzie.com.br",
                senha_hash=hash_senha("admin123"),
                telefone="(67) 99999-0000",
                nivel_id=niveis[3].id,  # administrador
                departamento_id=None,
                canal_id=None
            )
        ]
        db.add_all(usuarios)
        
        # Commit final
        db.commit()
        print("✅ Banco de dados inicializado com sucesso!")
        print(f"   - {len(niveis)} níveis criados")
        print(f"   - {len(departamentos)} departamentos criados")
        print(f"   - {len(canais)} canais criados")
        print(f"   - {len(usuarios)} usuários criados")
        print("\n📧 Usuário admin: admin@hospitalmackenzie.com.br / admin123")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erro ao inicializar banco: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
