SKILL: IMPLEMENTAÇÃO DA FUNÇÃO DE IDENTIFICAÇÃO DE STATUS DE CONTATO (RETORNO PENDENTE E EM ATENDIMENTO) NO ECOCHATMARCX
1. CONTEXTO E OBJETIVO
Você atuará como um Arquiteto de Software Sênior especialista em Angular, Python (FastAPI) e sistemas de atendimento ao cliente (Chatbot/Helpdesk).
Durante a análise de referência de mercado (ZigChat), identificou-se uma lacuna crítica no EcoChatMarcx: o sistema não identifica automaticamente quando um contato que está iniciando uma conversa já possui um retorno pendente (atendimento anterior sem sucesso com promessa de recontato) ou já está sendo atendido simultaneamente por outro colaborador.
Objetivo: Projetar e implementar a função identificarStatusContato(contatoId) e toda a infraestrutura de backend, frontend e regras de negócio necessárias para classificar, alertar e gerenciar esses cenários, evitando atendimentos duplicados e honrando compromissos de retorno.
2. DEFINIÇÃO DOS STATUS DO CONTATO
A função deve classificar o contato em um destes quatro estados mutuamente exclusivos (com prioridade definida):
Status
Prioridade
Significado
EM_ATENDIMENTO
1 (Máxima)
O contato já possui um atendimento em aberto (status = em_atendimento) com outro atendente neste exato momento.
RETORNO_PENDENTE
2
O último atendimento foi encerrado sem_sucesso, o cliente aceitou ser recontatado (deseja_retorno = true) e a data do atendimento é anterior ao dia atual.
NOVO
3
Primeiro contato do cliente ou sem histórico relevante de atendimento.
FINALIZADO
4
Último atendimento foi concluído com sucesso, sem pendências de retorno.
3. REGRAS DE NEGÓCIO (CRÍTICAS)
Exclusividade de Atendimento: Um contato só pode ter um atendimento com status em_atendimento por vez.
Condição de Retorno Pendente: O status RETORNO_PENDENTE só é válido se:
status_anterior == 'sem_sucesso'
deseja_retorno == true
data_fim_atendimento < data_atual (evita conflitos no mesmo dia).
Prioridade de Alerta: O status EM_ATENDIMENTO sempre sobrescreve e tem prioridade de exibição sobre RETORNO_PENDENTE.
Isolamento Multi-Tenant: Todas as consultas e validações devem ser estritamente filtradas pelo tenant_id do EcoChatMarcx.
Limpeza Automática: Ao abrir um atendimento a partir da lista de retornos pendentes, o sistema deve automaticamente invalidar o status de pendência (criando um novo registro de atendimento ou atualizando o flag).
4. MODELAGEM DE DADOS (BACKEND - PYTHON/SQLALCHEMY)
Extensão necessária no modelo de Atendimento (ou Ticket/Conversa):
class StatusAtendimento(str, Enum):
    EM_ATENDIMENTO = "em_atendimento"
    SEM_SUCESSO = "sem_sucesso"
    FINALIZADO = "finalizado"

class Atendimento(Base):
    __tablename__ = "atendimentos"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    contato_id = Column(UUID(as_uuid=True), ForeignKey("contatos.id"), nullable=False, index=True)
    atendente_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    
    status = Column(Enum(StatusAtendimento), nullable=False, index=True)
    data_inicio = Column(DateTime(timezone=True), nullable=False)
    data_fim = Column(DateTime(timezone=True), nullable=True)
    
    # Campos específicos para a regra de retorno
    deseja_retorno = Column(Boolean, default=False)
    data_retorno_sugerida = Column(Date, nullable=True)
    
    # Índices compostos para performance na identificação rápida
    __table_args__ = (
        Index('ix_atendimentos_contato_status', 'contato_id', 'status'),
        Index('ix_atendimentos_tenant_retorno', 'tenant_id', 'deseja_retorno', 'status'),
    )

    5. DESIGN DA API RESTFUL (FASTAPI)
5.1. Identificação de Status (Trigger ao receber mensagem)
GET /api/v1/contacts/{contato_id}/status

Headers: Authorization, X-Tenant-ID
Response 200 OK:
json
{
  "contato_id": "uuid",
  "status_classificacao": "EM_ATENDIMENTO", 
  "detalhes": {
    "atendente_atual": "Maria Silva",
    "atendimento_id": "uuid-atendimento-aberto"
  }
}
(Se for RETORNO_PENDENTE, detalhes retorna data_ultimo_contato e motivo)
5.2. Listagem de Retornos Pendentes (Painel do Atendente)

GET /api/v1/attendances/pending-returns

GET /api/v1/attendances/pending-returns


5.3. Resolução de Retorno (Ao abrir o chat)

PATCH /api/v1/attendances/{atendimento_id}/resolve-return
Ação: Marca o atendimento anterior como "tratado" e inicia um novo com status em_atendimento.


Ação: Marca o atendimento anterior como "tratado" e inicia um novo com status em_atendimento.
6. ARQUITETURA FRONTEND (ANGULAR)
6.1. Componentes Necessários
ContactStatusBadgeComponent: Exibido no card do contato na lista de conversas.
Vermelho: EM_ATENDIMENTO (ex: "🔴 Em atendimento com [Nome]")
Amarelo: RETORNO_PENDENTE (ex: "🟡 Solicitou retorno em [Data]")
PendingReturnsPanelComponent: Painel lateral ou aba no dashboard do atendente, listando os retornos pendentes com filtros de data.
ChatHeaderWarningComponent: Banner no topo da janela de chat ativa: "⚠️ Este contato solicitou retorno em [Data]. Último motivo: [Motivo]".
6.2. Serviço Angular (ContactStatusService)
Método checkContactStatus(contatoId: string) chamado via WebSocket ou polling assim que uma nova mensagem chega ou o atendente clica no contato.
Método getPendingReturns(filters) para alimentar o painel lateral.
7. FLUXO DE EXECUÇÃO PROPOSTO
Gatilho: Nova mensagem recebida do contato_id = X.
Consulta: Backend executa identificarStatusContato(X).
Verificação 1 (Concorrência): Existe Atendimento com contato_id = X e status = em_atendimento?
Sim: Retorna EM_ATENDIMENTO. Frontend exibe badge vermelho e bloqueia ou emite alerta severo antes de permitir que o novo atendente assuma.
Verificação 2 (Retorno): Não está em atendimento. O último atendimento tem status = sem_sucesso E deseja_retorno = true E data_fim < hoje?
Sim: Retorna RETORNO_PENDENTE. Frontend exibe badge amarelo e insere o contato no painel lateral de "Retornos Pendentes".
Ação do Atendente: Ao clicar no contato pendente, o frontend chama o endpoint resolve-return, que cria o novo atendimento e limpa a pendência visual.
8. CHECKLIST DE IMPLEMENTAÇÃO
Fase 1: Backend (Python/FastAPI)
Atualizar Model SQLAlchemy Atendimento com os novos campos e índices.
Criar Migration Alembic para aplicar as mudanças no PostgreSQL.
Implementar a lógica da função identificarStatusContato no Service Layer.
Criar endpoints: GET /contacts/{id}/status, GET /attendances/pending-returns, PATCH /attendances/{id}/resolve-return.
Garantir que todas as queries incluam a cláusula WHERE tenant_id = :tenant_id.
Criar testes unitários (pytest) cobrindo as 4 classificações de status e a regra de data < hoje.
Fase 2: Frontend (Angular)
Criar ContactStatusService e atualizar os Models TypeScript.
Desenvolver ContactStatusBadgeComponent com as cores e textos condicionais.
Desenvolver PendingReturnsPanelComponent com tabela, ordenação por data e paginação.
Integrar o banner de aviso no cabeçalho do componente de Chat ativo.
Disparar a checagem de status automaticamente ao selecionar um contato na lista.
Fase 3: Integração e UX
Testar o fluxo completo: simular atendimento sem sucesso -> marcar retorno -> simular nova mensagem no dia seguinte -> verificar alerta.
Testar a concorrência: dois atendentes tentando abrir o mesmo contato simultaneamente.
Validar a limpeza automática do status de "Retorno Pendente" após a abertura do chat.
9. CRITÉRIOS DE ACEITE
O sistema identifica e classifica corretamente os 4 status (NOVO, RETORNO_PENDENTE, EM_ATENDIMENTO, FINALIZADO).
O sistema impede ou alerta visivelmente quando um contato já está em EM_ATENDIMENTO com outro colaborador, exibindo o nome do atendente responsável.
A lista/painel de "Retornos Pendentes" é visível, filtrável e ordenada (mais antigos primeiro).
A marcação de RETORNO_PENDENTE é limpa automaticamente (ou arquivada) no momento em que um atendente abre a conversa desse contato.
Nenhuma regra de negócio vaza dados entre tenants diferentes (isolamento total).
10. PROMPT EMBUTIDO PARA DESENVOLVIMENTO FUTURO
Copie e use o texto abaixo ao delegar esta tarefa para um desenvolvedor ou outra IA, garantindo a manutenção do contexto do EcoChatMarcx:

Implemente no EcoChatMarcx (stack: Angular 17+ frontend, Python/FastAPI backend, PostgreSQL) a função de identificação de status de contato, acionada ao receber uma nova mensagem ou ao selecionar um contato. 

Regras obrigatórias:
1. Se o contato já possui um atendimento em aberto (status = 'em_atendimento') com outro colaborador no mesmo tenant, retornar status 'EM_ATENDIMENTO', identificar o atendente responsável e gerar um alerta visual severo no frontend, impedindo ou avisando antes de abrir um novo atendimento.
2. Se o último atendimento do contato foi encerrado com status = 'sem_sucesso', E o campo 'deseja_retorno' é true, E a 'data_fim' desse atendimento é estritamente anterior ao dia atual, retornar status 'RETORNO_PENDENTE'.
3. Contatos classificados como 'RETORNO_PENDENTE' devem alimentar um painel lateral "Retornos Pendentes" no dashboard do atendente, ordenado por data mais antiga primeiro.
4. Ao abrir a conversa de um contato com 'RETORNO_PENDENTE', o sistema deve chamar um endpoint que invalida essa pendência e inicia o novo atendimento.
5. Basear-se no modelo de dados de "atendimentos", estendendo-o com os campos 'deseja_retorno' (boolean) e 'data_retorno_sugerida' (date), garantindo índices compostos por (tenant_id, contato_id, status) para performance.
6. Garantir isolamento total de dados por tenant_id em todas as queries.

Implemente no EcoChatMarcx (stack: Angular 17+ frontend, Python/FastAPI backend, PostgreSQL) a função de identificação de status de contato, acionada ao receber uma nova mensagem ou ao selecionar um contato. 

Regras obrigatórias:
1. Se o contato já possui um atendimento em aberto (status = 'em_atendimento') com outro colaborador no mesmo tenant, retornar status 'EM_ATENDIMENTO', identificar o atendente responsável e gerar um alerta visual severo no frontend, impedindo ou avisando antes de abrir um novo atendimento.
2. Se o último atendimento do contato foi encerrado com status = 'sem_sucesso', E o campo 'deseja_retorno' é true, E a 'data_fim' desse atendimento é estritamente anterior ao dia atual, retornar status 'RETORNO_PENDENTE'.
3. Contatos classificados como 'RETORNO_PENDENTE' devem alimentar um painel lateral "Retornos Pendentes" no dashboard do atendente, ordenado por data mais antiga primeiro.
4. Ao abrir a conversa de um contato com 'RETORNO_PENDENTE', o sistema deve chamar um endpoint que invalida essa pendência e inicia o novo atendimento.
5. Basear-se no modelo de dados de "atendimentos", estendendo-o com os campos 'deseja_retorno' (boolean) e 'data_retorno_sugerida' (date), garantindo índices compostos por (tenant_id, contato_id, status) para performance.
6. Garantir isolamento total de dados por tenant_id em todas as queries.

Referência de comportamento: funcionalidade equivalente observada no ZigChat, adaptada para a arquitetura multi-tenant do EcoChatMarcx.


