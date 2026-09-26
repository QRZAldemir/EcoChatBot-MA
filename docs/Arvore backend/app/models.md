backend/app/models/
│
├── __init__.py                            🎯 Exporta TODOS os modelos (ordem respeita FKs)
├── base.py                                🧱 DeclarativeBase + naming convention Alembic
├── enums.py                               🔢 20 enums (status, perfis, tipos, motivos)
├── mixins.py                              ♻️  TimestampMixin · SoftDeleteMixin · TenantMixin
│
│   ─── TENANTS (raiz → filhas) ──────────────────────────────────────────
├── cliente_models.py                      🏢 Cliente (Tenant raiz — roadmap README §11)
├── empresa_models.py                      🏢 Empresa · Usuario · InstanciaChatbot
│
│   ─── ESTRUTURA ORGANIZACIONAL ─────────────────────────────────────────
├── contato_models.py                      📇 Contato (multi-canal por cliente)
├── departamento_models.py                 🏛️ Departamento (com expediente + cor)
│
│   ─── CONTRATO DE CANAIS (por onde a Empresa recebe) ───────────────────
├── canal_contratado_models.py             📡 CanalContratado (item do contrato)
├── conexao_models.py                      🔗 Conexao (estado + histórico do socket)
│
│   ─── FLUXO DO CLIENTE (menu → roteiro → atendimento) ──────────────────
├── menu_models.py                         🍔 Menu · MenuItem (opção → departamento)
├── roteiro_models.py                      🗺️  Roteiro (metadados do HTML de perguntas)
│
│   ─── ATENDIMENTO (coração do sistema) ─────────────────────────────────
├── atendimento_models.py                  🎧 Atendimento (conversa)
├── atendimento_context_models.py          📝 AtendimentoContexto (respostas do roteiro)
├── chamada_pabx_models.py                 📞 ChamadaPABX (VoIP — entrada/saída/interna)
│
│   ─── CONTEÚDO E AUTOMAÇÃO ─────────────────────────────────────────────
├── modelo_mensagem_models.py              💬 ModeloMensagem (templates)
├── campanha_models.py                     📢 Campanha (disparo em massa)
├── pedido_models.py                       🛒 Pedido · PedidoItem
├── email_models.py                        📧 EmailTemplate · EmailLog
└── token_revogado_models.py               🚫 TokenRevogado (blacklist JWT)