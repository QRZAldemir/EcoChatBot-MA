"""
Dados de seed usados por init_db.py para popular um banco recém-criado.

Este módulo só contém dados (nenhuma lógica) - a orquestração de quem é
criado, em que ordem e sob quais condições fica em init_db.py.
"""

NIVEIS_DATA = [
    {"nome": "atendente", "descricao": "Atendente de suporte"},
    {"nome": "supervisor", "descricao": "Supervisor de equipe"},
    {"nome": "gerente", "descricao": "Gerente de operações"},
    {"nome": "administrador", "descricao": "Administrador do sistema"}
]

DEPARTAMENTOS_DATA = [
    {"nome": "Call-Center", "descricao": "Central de atendimento telefônico"},
    {"nome": "Recepção", "descricao": "Recepção e portaria do hospital"},
    {"nome": "Ouvidoria", "descricao": "Ouvidoria e relações com pacientes"},
    {"nome": "Agendamento", "descricao": "Agendamento de consultas e exames"},
    {"nome": "Exames", "descricao": "Centro de diagnósticos e exames"}
]

# Os canais referenciam os departamentos pelo nome (chave estrangeira lógica)
CANAIS_DATA = [
    {"nome": "Atendimento-Cliente", "descricao": "Canal de atendimento geral ao cliente", "arquivo_menu": "1atendimento-ma.html", "depto_ref": "Call-Center"},
    {"nome": "Agendamento-Ambulatorial", "descricao": "Agendamento de consultas ambulatoriais", "arquivo_menu": "2agendamento-ma.html", "depto_ref": "Agendamento"},
    {"nome": "Exames-Diagnostico", "descricao": "Agendamento e resultados de exames", "arquivo_menu": "3examesdiagnostico-ma.html", "depto_ref": "Exames"},
    {"nome": "Portaria", "descricao": "Controle de acesso e informações da portaria", "arquivo_menu": "7portaria-ma.html", "depto_ref": "Recepção"},
    {"nome": "Ouvidoria", "descricao": "Canal de ouvidoria para reclamações e sugestões", "arquivo_menu": "8ouvidoria-ma.html", "depto_ref": "Ouvidoria"}
]

# Conta de bootstrap: é a única forma de logar no sistema recém-criado e, a
# partir dela, cadastrar os usuários reais pela tela de administração. Por
# isso é sempre criada por init_db.py, independente de SEED_DEMO_USERS.
#
# A senha abaixo é texto puro só neste arquivo-fonte; init_db.py converte
# para hash (bcrypt) antes de gravar no banco. Ainda assim, por ficar
# visível no código/histórico do git, troque-a via variável de ambiente
# (ADMIN_SENHA) e force a troca no primeiro login antes de expor o
# ambiente publicamente - nunca use "admin123" em produção.
ADMIN_DATA = {
    "nome": "Carlos Admin", "email": "admin@hospitalmarcx.com.br", "senha": "admin123",
    "telefone": "(67) 99999-0000", "nivel_ref": "administrador", "depto_ref": None, "canal_ref": None
}

# Usuários de demonstração: um atendente por canal, para permitir testar
# cada fluxo de atendimento (Call-Center, Recepção, Ouvidoria, Agendamento,
# Exames) sem precisar cadastrar usuários manualmente pela tela de admin.
# NÃO são cadastros reais - só são criados quando SEED_DEMO_USERS=true
# (ver init_db.py). Mantenha desligado em produção.
USUARIOS_DEMO_DATA = [
    {"nome": "Ana Silva", "email": "ana@hospitalmarcx.com.br", "senha": "senha123", "telefone": "(67) 99999-1111", "nivel_ref": "atendente", "depto_ref": "Call-Center", "canal_ref": "Atendimento-Cliente"},
    {"nome": "João Santos", "email": "joao@hospitalmarcx.com.br", "senha": "senha123", "telefone": "(67) 99999-2222", "nivel_ref": "atendente", "depto_ref": "Recepção", "canal_ref": "Portaria"},
    {"nome": "Francisca Oliveira", "email": "francisca@hospitalmarcx.com.br", "senha": "senha123", "telefone": "(67) 99999-3333", "nivel_ref": "atendente", "depto_ref": "Ouvidoria", "canal_ref": "Ouvidoria"},
    {"nome": "Daniele Costa", "email": "daniele@hospitalmarcx.com.br", "senha": "senha123", "telefone": "(67) 99999-4444", "nivel_ref": "atendente", "depto_ref": "Agendamento", "canal_ref": "Agendamento-Ambulatorial"},
    {"nome": "Aldemir Pereira", "email": "aldemir@hospitalmarcx.com.br", "senha": "senha123", "telefone": "(67) 99999-5555", "nivel_ref": "atendente", "depto_ref": "Exames", "canal_ref": "Exames-Diagnostico"}
]
