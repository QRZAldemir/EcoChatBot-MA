1. CONTEXTO E PROPÓSITO
Esta skill define a estrutura de dados, as regras de negócio e os padrões arquiteturais do EcoChatMarcx. O sistema evoluiu de uma solução vertical (hospitalar) para uma plataforma SaaS horizontal (genérica), adaptável a qualquer modelo de negócio (clínicas, varejo, educação, serviços, etc.). O foco central é o atendimento omnichannel (com ênfase em WhatsApp via Evolution API), gestão de tickets, automação de menus, campanhas de disparo e gestão de turnos/equipes.
⚠️ REGRA DE OURO (DÍVIDA TÉCNICA RESOLVIDA):
Nunca utilizar o mesmo identificador para uma Column (coluna de banco) e um relationship (relacionamento ORM) na mesma classe. O sistema sofreu previamente com isso na entidade Atendimento. A coluna que armazena o identificador deve possuir sufixo explícito (ex: tipo_canal, canal_id), distinguindo-se do objeto de relacionamento (ex: canal).
2. PRINCÍPIOS ARQUITETURAIS GLOBAIS
Multi-Tenancy e Isolamento: Embora o modelo atual utilize empresa_id ou contextos isolados, a evolução SaaS exige que todas as queries de negócio filtrem obrigatoriamente pelo identificador do tenant/empresa para evitar vazamento de dados entre clientes.
Soft Delete: Entidades de negócio não são removidas fisicamente. Utiliza-se o campo ativo = Column(Boolean, default=True). Operações de exclusão devem realizar UPDATE ativo = False.
Auditoria Temporal: Entidades críticas possuem criado_em e atualizado_em (com onupdate=datetime.utcnow).
Abstração de Domínio: Termos médicos legados (ex: "Pediatria", "Ginecologia", "NIR") devem ser abstraidos para conceitos genéricos de negócio (ex: "Departamentos", "Canais", "Equipes de Plantão").
3. MAPEAMENTO DE DOMÍNIOS E ENTIDADES (ORM)
3.1. Núcleo de Atendimento (Core Ticketing)
Atendimento: Representa um ticket ou interação com o cliente.
Campos Críticos: protocolo (único), status ("aberto", "fila", "em_atendimento", "finalizado"), tipo (1=automático/bot, 2=manual/humano).
Abstração: O campo tipo_canal (1=WhatsApp, 2=Interno) define a origem. O relacionamento canal traz os metadados do ponto de contato.
AtendimentoContext: Armazenamento de estado dinâmico (chave-valor) da conversa, utilizado pelo motor do bot para rastrear a jornada do usuário dentro de um menu.
3.2. Estrutura Organizacional e RBAC (Controle de Acesso)
NivelUsuario: Hierarquia de papéis (atendente, supervisor, gerente, administrador).
Departamento: Unidades de negócio ou centros de custo (ex: "Vendas", "Suporte", "Triagem").
Canal: Pontos de contato específicos vinculados a um departamento (ex: "WhatsApp Loja 1", "Instagram Oficial"). Define o arquivo_menu (protótipo de fluxo) a ser utilizado.
Usuario: Operadores do sistema. Vinculados a um nivel_id, departamento_id e, opcionalmente, a um canal_id específico.
3.3. Automação e Fluxos Interativos
Menu e MenuOpcao: Representam a árvore de decisão do Chatbot. Vinculados a um canal_id. As opções possuem row_id (gatilho de ação), ordem e cor (para renderização UI).
ModeloMensagem: Templates de texto (memorandos/respostas rápidas) pré-cadastrados, vinculados a um departamento_id, permitindo reutilização e padronização da comunicação.
3.4. Infraestrutura de Conexão e CRM
Conexao: Representa uma instância de mensageria (ex: número WhatsApp via Evolution API).
Regra de Negócio: O campo padrao (Boolean) indica o número principal. Apenas uma conexão pode ser padrão por vez (lógica a ser garantida no Service layer).
Contato: Base de clientes (CRM). Campo origem ("manual" ou "atendimento"). Serve como base para campanhas.
Arquivo: Biblioteca de mídia compartilhada, vinculada opcionalmente a um atendimento.
3.5. Módulo de Campanhas (Marketing/Outbound)
Campanha: Disparo em massa. Vinculado a uma conexao_id. Rastreia métricas (total_contatos, enviados, falhas) e status ("rascunho", "enviando", "concluida").
CampanhaContato: Tabela de associação (N:N) que rastreia o status individual de entrega para cada destinatário na campanha.
3.6. Utilitários, Segurança e Legado
TokenRevogado: Blacklist de JWTs (armazena jti e expira_em) para garantir a invalidação real no logout.
EmailEnviado: Log de e-mails transacionais.
Módulo de Escalas (Legado/Genérico): O módulo de "Escalas Médicas" presente no HTML legado deve ser refatorado para Gestão de Turnos e Equipes. As especialidades (Pediatria, Adulto, GO) devem tornar-se "Departamentos" ou "Equipes" configuráveis, e os turnos (Manhã, Tarde, Noite) devem ser parâmetros de configuração do tenant, não hardcoded.
4. DIRETRIZES DE IMPLEMENTAÇÃO (PARA IA E DESENVOLVEDORES)
Ao gerar código (Schemas Pydantic, Services, Controllers ou Migrações Alembic) para o EcoChatMarcx, siga estritamente estas diretrizes:
A. Schemas Pydantic (Validação e Serialização)
Separação de Criação/Atualização vs. Resposta:
Create/Update Schemas: Devem aceitar apenas IDs inteiros (ex: canal_id: int), nunca objetos aninhados.
Response Schemas: Devem utilizar from_attributes = True e expor dados enriquecidos de forma segura (ex: canal_nome: str | None).
Validação de Limites: Respeitar rigorosamente os limites definidos no ORM (ex: String(100) deve ser Field(max_length=100) no Pydantic).
B. Camada de Serviço (Regras de Negócio)
Exclusividade de Recursos: Ao manipular flags de exclusividade (ex: Conexao.padrao = True), o Service deve primeiro neutralizar os registros existentes (UPDATE ... SET padrao = False WHERE padrao = True) antes de persistir a nova entidade.
Transições de Estado: Validar máquinas de estado. Ex: Um Atendimento não pode transicionar de "finalizado" para "em_atendimento" sem uma reabertura formal.
Soft Delete: Endpoints de deleção (DELETE /resource/{id}) devem ser implementados como PATCH /resource/{id} alterando ativo=False.
C. Camada de Repositório (Consultas SQLAlchemy)
Filtros Padrão: Incluir ativo == True por padrão em todas as queries de listagem, exceto em rotas administrativas explícitas.
Otimização de Carregamento (N+1): Utilizar selectinload ou joinedload ao buscar listas que exijam dados de relacionamento.

   # Exemplo de boas práticas:
   stmt = select(Atendimento).options(
       selectinload(Atendimento.canal), 
       selectinload(Atendimento.usuario)
   ).where(Atendimento.ativo == True)


   D. Migrações de Banco de Dados (Alembic)
Integridade Referencial: Garantir que ForeignKey e relationship (com back_populates) sejam criados em pares.
Enums e Constraints: Para campos como status em Atendimento, preferir Enum nativo do banco ou CheckConstraint para garantir a consistência dos valores permitidos.
5. CHECKLIST DE VALIDAÇÃO DE FEATURES
Antes de submeter ou gerar uma nova funcionalidade que interaja com o domínio do EcoChatMarcx, validar:
A entidade possui id, criado_em e ativo (se aplicável)?
Os relacionamentos possuem back_populates definidos em ambas as extremidades?
Não há conflito de nomes entre Column e relationship na mesma classe?
O Schema Pydantic reflete os tipos primitivos (int, str) e não instâncias do ORM?
A lógica de negócio está abstraída de termos médicos, sendo aplicável a qualquer setor (varejo, serviços, etc.)?
Operações de "exclusão" implementam Soft Delete?
Instrução de Uso: Este documento deve ser injetado no contexto de qualquer sessão de desenvolvimento, code review ou geração de código por IA, garantindo que a evolução do EcoChatMarcx mantenha a coerência arquitetural, a escalabilidade SaaS e a independência de modelos de negócio específicos.