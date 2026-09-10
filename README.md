<<<<<<< HEAD
# EcoChatBot-MA
=======
# EcoChatBotMarcx
>>>>>>> 37038798148d95e3284b5959b5d7ab66266a4507
## Sistema de Atendimento Digital Configurável
### Adaptável para qualquer segmento: saúde, comércio, serviços, indústria, instituições e mais

---

## ÍNDICE

1. APRESENTAÇÃO
2. CONCEITO E FLUXO DE FUNCIONAMENTO
3. COMO FUNCIONA A CONFIGURAÇÃO
4. ESTADO ATUAL DO PROJETO
5. ESTRUTURA DE PASTAS E ARQUIVOS
6. CANAIS E ROTEIROS DE ATENDIMENTO
7. GUIA DE INSTALAÇÃO
8. TECNOLOGIAS UTILIZADAS
9. VARIÁVEIS DE AMBIENTE
10. PAINEL ANALÍTICO E RELATÓRIOS
11. EVOLUÇÃO E PERSPECTIVAS

---

## 1. APRESENTAÇÃO

O **EcoChatBot-MA** é um sistema de atendimento digital inteligente e 100% configurável, projetado para servir qualquer tipo de negócio. Não é necessário programar fluxos: basta cadastrar setores, definir tipos de atendimento e criar roteiros personalizados — e o sistema estará pronto para funcionar.

### Como funciona de forma simples
O cliente entra em contato pelo WhatsApp e recebe um menu com opções. Ele toca na opção desejada sem precisar digitar nada. O sistema identifica a escolha, encaminha automaticamente para o setor e pessoa responsável, e carrega o formulário de perguntas adequado. O atendente recebe todos os dados coletados de forma organizada e conduz o atendimento com agilidade.

### Diferenciais
- Sem programação de fluxos — configure apenas cadastrando informações
- Reutilizável para qualquer ramo de atividade
- Inteligência artificial integrada como assistente
- Acompanhamento em tempo real e relatórios completos

---

## 2. CONCEITO E FLUXO DE FUNCIONAMENTO

O fluxo universal do EcoChatBot-MA funciona nesta sequência:

1. Contato inicial — O cliente envia mensagem pelo WhatsApp
2. Apresentação do menu — O sistema responde com menu de opções personalizado do negócio
3. Escolha do tipo de atendimento — Cliente seleciona a opção desejada tocando no botão
4. Identificação do canal — Sistema reconhece a qual tipo de atendimento corresponde aquela escolha
5. Carregamento do roteiro — São apresentadas as perguntas e informações necessárias para aquele tipo de atendimento
6. Encaminhamento inteligente — O sistema localiza um atendente disponível vinculado àquele canal e setor
7. Abertura no painel — A conversa é aberta no painel web do atendente, já com todos os dados preenchidos
8. Atendimento e conclusão — Atendente responde, interage e finaliza o atendimento

Representação sequencial:

CLIENTE (WhatsApp)
    │
    ├─ Envia mensagem inicial
    │
    ▼
SISTEMA → Apresenta MENU com opções
    │
    │  Cliente SELECIONA uma opção tocando no botão
    │
    ▼
WHATSAPP API → Envia a escolha ao sistema
    │
    ▼
BACKEND → Reconhece o CANAL selecionado e carrega o ROTEIRO correspondente
    │
    ▼
BACKEND → Localiza ATENDENTE disponível no setor responsável
    │
    ▼
PAINEL WEB → Abre o atendimento com todos os dados coletados e organizados
    │
    ▼
ATENDENTE → Conduz a conversa, responde ao cliente e finaliza o atendimento

---

## 3. COMO FUNCIONA A CONFIGURAÇÃO

Todo o poder de adaptação do EcoChatBot-MA está em três elementos simples que você cadastra:

| Elemento | O que representa | Exemplo para Loja | Exemplo para Clínica |
|---|---|---|---|
| DEPARTAMENTO | Setor ou equipe responsável pelo atendimento | Vendas, Financeiro, Entregas | Recepção, Consultas, Exames |
| CANAL | Tipo de atendimento com nome visível ao cliente | Orçamento, Reclamação, Suporte | Agendamento, Retorno, Ouvidoria |
| ROTEIRO | Arquivo com perguntas e fluxo específicos | orcamento-loja.html | agendamento-clinica.html |

Você altera apenas estes três elementos e o sistema se adapta ao seu negócio. Sem precisar mudar nenhum código de programação.

---

## 4. ESTADO ATUAL DO PROJETO

| Componente | Situação | Detalhe |
|---|---|---|
| Estrutura de roteiros | Pronto | Estrutura genérica pronta para personalização |
| Painel Web em Angular | Estruturado | Telas de administração, atendimento e relatórios |
| API Backend em FastAPI | Estruturado | Endpoints, regras de negócio e integrações |
| Banco de Dados PostgreSQL | Pendente | Aguardando instalação e configuração |
| Integração com WhatsApp | Pendente | Aguardando credenciais de API |
| Inteligência Artificial | Pendente | Aguardando configuração de chave de acesso |

---

## 5. ESTRUTURA DE PASTAS E ARQUIVOS

EcoChatBot-MA/
│
├── roteiros/
│   ├── hub_Menu.html
│   ├── atendimento.html
│   ├── agendamento.html
│   ├── informacoes.html
│   ├── financeiro.html
│   ├── suporte.html
│   └── personalize conforme a necessidade do negócio
│
├── frontend/
│   └── src/
│       ├── main.ts
│       ├── index.html
│       └── app/
│           ├── app.component.ts
│           ├── app.routes.ts
│           ├── core/
│           │   ├── models/
│           │   │   ├── usuario.model.ts
│           │   │   ├── departamento.model.ts
│           │   │   ├── canal.model.ts
│           │   │   └── nivel-usuario.model.ts
│           │   └── services/
│           │       ├── usuario.service.ts
│           │       ├── departamento.service.ts
│           │       ├── canal.service.ts
│           │       └── ia.service.ts
│           ├── pages/
│           │   ├── admin/
│           │   │   ├── dashboard/
│           │   │   ├── usuarios/
│           │   │   ├── departamentos/
│           │   │   ├── canais/
│           │   │   ├── niveis/
│           │   │   ├── horarios/
│           │   │   └── relatorios/
│           │   └── atendimento/
│           │       ├── menu/
│           │       └── conversa/
│           └── shared/
│               └── components/layout/
│
├── backend/
│   ├── requirements.txt
│   ├── .env.example
│   ├── init_db.py
│   ├── seed_data.py
│   ├── run_migrations.py
│   ├── export_openapi.py
│   ├── migrations/
│   └── app/
│       ├── main.py
│       ├── database.py
│       ├── models/
│       ├── schemas/
│       ├── services/
│       │   ├── usuario_service.py
│       │   ├── departamento_service.py
│       │   ├── canal_service.py
│       │   ├── atendimento_service.py
│       │   ├── roteiro_service.py
│       │   ├── bot_service.py
│       │   ├── ia_service.py
│       │   ├── whatsapp_service.py
│       │   └── audio_service.py
│       └── routers/
│           ├── auth.py
│           ├── usuarios.py
│           ├── departamentos.py
│           ├── canais.py
│           ├── atendimento.py
│           ├── webhook.py
│           ├── ia.py
│           ├── mensagens.py
│           ├── roteiros.py
│           └── audio.py
│
├── docs/
│   ├── arquitetura.md
│   ├── guia-configuracao.md
│   └── modelos-de-negocio.md
│
└── painel-analitico/
    └── dashboard.html

---

## 6. CANAIS E ROTEIROS DE ATENDIMENTO

Você define seus próprios canais conforme a necessidade do seu negócio. Abaixo exemplos de estrutura:

| Canal de Atendimento | Roteiro Vinculado | Objetivo do Fluxo |
|---|---|---|
| Atendimento Geral | atendimento.html | Informações gerais, dúvidas e contato |
| Agendamento ou Reserva | agendamento.html | Marcar, confirmar, remarcar ou cancelar |
| Pedidos e Orçamentos | pedidos.html | Solicitar valores, condições e prazos |
| Financeiro | financeiro.html | Emissão de documentos, pagamento e negociação |
| Suporte Técnico | suporte.html | Resolução de problemas e dúvidas técnicas |
| Ouvidoria e Feedback | ouvidoria.html | Reclamações, elogios e sugestões |

Para adaptar ao seu negócio: crie o roteiro HTML com suas perguntas e cadastre o canal com o nome que desejar. Nenhuma alteração no código é necessária.

---

## 7. GUIA DE INSTALAÇÃO

Passo 1 — Preparar o ambiente
- Instalar Python versão 3.10 ou superior, Node.js e PostgreSQL
- Criar banco de dados com o nome ecochatbot_ma

Passo 2 — Instalar e configurar o Backend
- Acessar a pasta backend pelo terminal
- Criar ambiente virtual: python3 -m venv venv
- Ativar o ambiente virtual: source venv/bin/activate
- Instalar dependências: pip install -r requirements.txt
- Copiar arquivo de exemplo: cp .env.example .env
- Editar o arquivo .env com suas credenciais e configurações
- Criar estrutura do banco: python3 init_db.py
- Carregar dados padrão: python3 seed_data.py
- Iniciar a API: uvicorn app.main:app --reload --port 8000
- A API estará acessível em http://localhost:8000 e a documentação em http://localhost:8000/docs

Passo 3 — Instalar e configurar o Frontend
- Acessar a pasta frontend pelo terminal
- Instalar pacotes: npm install
- Gerar cliente de API: npm run generate:api
- Iniciar o painel: ng serve
- O painel estará acessível em http://localhost:4200

Passo 4 — Configurar integração com WhatsApp
- Obter credenciais na plataforma oficial da Meta ou na Evolution API
- Preencher os dados no arquivo .env com os códigos e tokens recebidos
- Cadastrar o endereço do webhook fornecido pelo sistema

Passo 5 — Ativar Inteligência Artificial
- Obter chave de acesso na plataforma de inteligência artificial escolhida
- Registrar a chave no arquivo de variáveis de ambiente

Passo 6 — Adaptar o sistema ao seu negócio
1. Cadastrar os Departamentos correspondentes ao seu negócio
2. Cadastrar os Canais de atendimento vinculando aos respectivos roteiros
3. Criar ou ajustar os arquivos HTML dos roteiros com suas perguntas
4. Vincular cada atendente ao canal e departamento correspondente
5. Definir os horários de atendimento por departamento

---

## 8. TECNOLOGIAS UTILIZADAS

| Camada do Sistema | Tecnologia Empregada | Versão | Motivo da Escolha |
|---|---|---|---|
| Painel Web | Angular | 17 | Estruturado, moderno e de alta performance |
| Linguagem Frontend | TypeScript | 5.4 | Maior segurança e produtividade no desenvolvimento |
| Estilização | CSS personalizável | Livre | Permite aplicar a identidade visual do cliente |
| API Backend | FastAPI | 0.109+ | Alta velocidade, operações assíncronas e documentação automática |
| Linguagem Backend | Python | 3.10+ | Simplicidade de manutenção e ampla integração com inteligência artificial |
| Gerenciamento de Dados | SQLAlchemy | 2.0 | Modelagem robusta e independente do banco de dados |
| Validação de Informações | Pydantic | 2.5 | Garante consistência e qualidade dos dados recebidos |
| Banco de Dados | PostgreSQL | 15+ | Banco relacional mais confiável, seguro e escalável disponível |
| Inteligência Artificial | API configurável pelo usuário | Variável | Funciona com diferentes plataformas conforme preferência |
| Mensagens Instantâneas | WhatsApp API ou Evolution API | Variável | Integração com o canal de comunicação mais utilizado no Brasil |

---

## 9. VARIÁVEIS DE AMBIENTE

Conteúdo do arquivo backend/.env que deverá ser preenchido com suas informações:

DATABASE_URL=endereco_do_banco_de_dados_com_usuario_e_senha
IA_API_KEY=chave_de_acesso_da_inteligencia_artificial
IA_MODELO=nome_do_modelo_de_ia_desejado
WHATSAPP_PHONE_ID=numero_ou_identificador_recebido_na_api
WHATSAPP_TOKEN=token_de_acesso_da_api_do_whatsapp
WHATSAPP_VERIFY_TOKEN=codigo_secreto_para_verificacao_do_webhook
SECRET_KEY=chave_aleatoria_e_secreta_para_seguranca_do_sistema
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

---

## 10. PAINEL ANALÍTICO E RELATÓRIOS

O painel analítico lê os dados armazenados e apresenta as seguintes informações:

Situações de Atendimento:
- Aguardando: cliente iniciou o contato mas ainda não possui atendente designado
- Em Andamento: atendente foi designado e está conduzindo a conversa
- Finalizado: atendimento foi concluído e encerrado oficialmente

Alertas e Observações:
- Horário de atendimento configurável individualmente por departamento
- Alerta de Fora do Expediente: atendimento recebido fora do horário definido
- Alerta de Sem Roteamento: atendimento aberto sem ter sido identificado claramente o canal
- Alerta de Pendência Prolongada: atendimento aberto há mais de 24 horas sem conclusão
- Alerta de Sem Responsável: atendimento existe mas não possui vínculo com departamento nem atendente

Motivos mais comuns em que o atendimento não é roteado automaticamente:
1. Mensagem recebida fora do horário de funcionamento definido
2. Cliente não conseguiu ou não selecionou claramente uma opção de canal

Relatórios Disponíveis:
- Resumo de volume de atendimentos por departamento e por canal
- Taxa de conclusão e tempo médio de duração dos atendimentos
- Pontos de atenção e sugestões de melhoria nos processos de atendimento
- Datas e períodos apresentados no formato brasileiro dia, mês e ano

---

## 11. EVOLUÇÃO E PERSPECTIVAS

Versão Atual: Sistema completamente configurável por meio de cadastros. Basta informar setores, canais e roteiros para adaptar a qualquer tipo de negócio sem programação.

Próximas Etapas de Evolução Prevista:
- Implementar suporte a Multi-Empresa ou Multi-Tenant para que uma instalação atenda vários negócios ao mesmo tempo
- Desenvolver Construtor Visual de Roteiros permitindo criar fluxos de atendimento sem precisar editar arquivos HTML
- Disponibilizar Integrações Prontas com sistemas de pagamento, agendas, ERPs e plataformas de comércio eletrônico
<<<<<<< HEAD
- Aprimorar a Inteligência Artificial para aprender com o próprio histórico de atendimentos e responder de forma autônoma e personalizada
=======
- Aprimorar a Inteligência Artificial para aprender com o próprio histórico de atendimentos e responder de forma autônoma e personalizada
>>>>>>> 37038798148d95e3284b5959b5d7ab66266a4507
