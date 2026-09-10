"""
Dados de seed usados por init_db.py para popular um banco recém-criado.

Este módulo só contém dados (nenhuma lógica) - a orquestração de quem é
criado, em que ordem e sob quais condições fica em init_db.py.

Os departamentos/canais abaixo são um exemplo genérico de SaaS (suporte,
comercial, financeiro, SAC). Cada tenant cadastra os seus pela tela admin.
"""

NIVEIS_DATA = [
    {"nome": "atendente", "descricao": "Atendente de suporte"},
    {"nome": "supervisor", "descricao": "Supervisor de equipe"},
    {"nome": "gerente", "descricao": "Gerente de operações"},
    {"nome": "administrador", "descricao": "Administrador do sistema"}
]

DEPARTAMENTOS_DATA = [
    {"nome": "Suporte", "descricao": "Atendimento e suporte ao cliente"},
    {"nome": "Comercial", "descricao": "Vendas, propostas e onboarding"},
    {"nome": "Financeiro", "descricao": "Cobrança, notas e pagamentos"},
    {"nome": "SAC", "descricao": "Ouvidoria, reclamações e elogios"},
]

# Os canais referenciam os departamentos pelo nome (chave estrangeira lógica).
# arquivo_menu é opcional: o fluxo do WhatsApp vem do cadastro de Mensagens.
CANAIS_DATA = [
    {"nome": "Atendimento", "descricao": "Canal geral de atendimento ao cliente", "arquivo_menu": "", "depto_ref": "Suporte"},
    {"nome": "Comercial", "descricao": "Vendas e propostas", "arquivo_menu": "", "depto_ref": "Comercial"},
    {"nome": "Financeiro", "descricao": "Cobrança e pagamentos", "arquivo_menu": "", "depto_ref": "Financeiro"},
    {"nome": "SAC", "descricao": "Reclamações, elogios e sugestões", "arquivo_menu": "", "depto_ref": "SAC"},
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
    "nome": "Admin", "email": "admin@ecochat.local", "senha": "admin123",
    "telefone": "(11) 99999-0000", "nivel_ref": "administrador", "depto_ref": None, "canal_ref": None
}

# Usuários de demonstração: um atendente por canal. NÃO são cadastros reais
# — só são criados quando SEED_DEMO_USERS=true (ver init_db.py).
USUARIOS_DEMO_DATA = [
    {"nome": "Ana Silva", "email": "ana@ecochat.local", "senha": "senha123", "telefone": "(11) 99999-1111", "nivel_ref": "atendente", "depto_ref": "Suporte", "canal_ref": "Atendimento"},
    {"nome": "João Santos", "email": "joao@ecochat.local", "senha": "senha123", "telefone": "(11) 99999-2222", "nivel_ref": "atendente", "depto_ref": "Comercial", "canal_ref": "Comercial"},
    {"nome": "Francisca Oliveira", "email": "francisca@ecochat.local", "senha": "senha123", "telefone": "(11) 99999-3333", "nivel_ref": "atendente", "depto_ref": "Financeiro", "canal_ref": "Financeiro"},
    {"nome": "Daniele Costa", "email": "daniele@ecochat.local", "senha": "senha123", "telefone": "(11) 99999-4444", "nivel_ref": "atendente", "depto_ref": "SAC", "canal_ref": "SAC"},
]
