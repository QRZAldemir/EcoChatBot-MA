/**
 * ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 * EcoChatBot-Marcx · Auth Barrel
 * Codinome: EcoChatBot-MA
 * ───────────────────────────────────────────────────────────────────────────
 * @file     index.auth.ts
 * @module   Core / Auth / Exports
 * @author   Aldemir Queiroz
 * @since    2026
 * @version  1.0.0
 * ───────────────────────────────────────────────────────────────────────────
 *
 * FUNCIONALIDADE
 * ──────────────
 * Barrel file (ponto de entrada público) da camada de AUTENTICAÇÃO e
 * SESSÃO do EcoChatBot-Marcx.
 *
 * Centraliza os exports de:
 *   • Facade de sessão         → SessionsFacade
 *   • Storage do token         → TokenStorage
 *   • Guards                   → authGuard, nivelGuard
 *   • Utilitários de hierarquia → NIVEIS_HIERARQUIA, ordemNivel, temNivelMinimo
 *   • Modelos da sessão        → SessionSnapshot, SessionStatus, LoginCredentials
 *
 * OBJETIVO
 * ────────
 * Permitir que features e outros módulos importem TUDO da camada auth
 * com um único caminho:
 *
 *   import { SessionsFacade, authGuard } from '@core/auth';
 *
 * Em vez de:
 *   import { SessionsFacade } from '@core/auth/sessions.facade';
 *   import { authGuard }      from '@core/auth/guards/auth.guard';
 *
 * ⚠️ REGRAS DO BARREL
 * ───────────────────
 *   • Features importam SOMENTE deste arquivo (nunca de dentro).
 *   • Dentro da própria camada auth, imports continuam RELATIVOS.
 *   • Nunca importar de `@core/auth/guards/auth.guard` diretamente.
 *
 * ⚠️ ESCOPO MULTI-CANAL E MULTI-SEGMENTO
 * ─────────────────────────────────────
 * A camada auth é agnóstica de canal e segmento. O que ela exporta
 * funciona igualmente em WhatsApp, Telegram, Discord, Facebook,
 * Instagram, PABX — e em qualquer segmento de negócio (saúde,
 * financeiro, varejo, educação, jurídico, turismo, governo, serviços).
 *
 * ESTRUTURA INTERNA DA CAMADA
 * ───────────────────────────
 *   core/auth/
 *   ├── sessions.facade.ts        → SessionsFacade (orquestrador)
 *   ├── token.storage.ts          → TokenStorage (persistência)
 *   ├── niveis.auth.ts            → utilitários de hierarquia
 *   ├── index.auth.ts             → este arquivo (barrel)
 *   │
 *   ├── guards/
 *   │   ├── auth.guard.ts         → authGuard
 *   │   ├── nivel.guard.ts        → nivelGuard
 *   │   ├── public-only.guard.ts  → publicOnlyGuard (futuro)
 *   │   └── role.guard.ts         → roleGuard (futuro)
 *   │
 *   └── models/
 *       └── session.model.ts      → SessionSnapshot, SessionStatus, ...
 *
 * FLUXO DE IMPORTAÇÃO
 * ───────────────────
 *   ┌─────────────────────────────────────────────────────────────────┐
 *   │  LoginComponent                                                │
 *   │    └─→ import { SessionsFacade } from '@core/auth'  ✅         │
 *   │                                                                │
 *   │  app.routes.ts                                                 │
 *   │    └─→ import { authGuard, nivelGuard } from '@core/auth' ✅   │
 *   │                                                                │
 *   │  NUNCA:                                                        │
 *   │    └─→ import { ... } from '@core/auth/sessions.facade'  ❌    │
 *   └─────────────────────────────────────────────────────────────────┘
 *
 * QUEM GERA
 * ─────────
 * Arquivo CUSTOM (não é gerado pelo codegen).
 * Documentação mantida manualmente junto ao time.
 *
 * ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 */

/* ═══════════════════════════════════════════════════════════════════════
 * 1. FACADE E STORAGE
 * ═══════════════════════════════════════════════════════════════════════
 * Serviços principais da sessão do operador.
 * Ambos são singletons (providedIn: 'root').
 */

/**
 * Orquestrador central do ciclo de vida da sessão do operador.
 *
 * Responsabilidades:
 *   • Autenticar (login) via AutenticacaoService (codegen)
 *   • Persistir JWT e perfil via TokenStorage
 *   • Manter estado reativo (session$)
 *   • Implementar SessionProvider para o token.resolver
 *   • Encerrar sessão (logout)
 */
export { SessionsFacade } from './sessions.facade';

/**
 * Persistência do JWT e do perfil do operador.
 * Abstrai o localStorage e isola a facade de qualquer detalhe de storage.
 */
export { TokenStorage } from './token.storage';

/* ═══════════════════════════════════════════════════════════════════════
 * 2. GUARDS DE AUTENTICAÇÃO E AUTORIZAÇÃO
 * ═══════════════════════════════════════════════════════════════════════
 * Guards são funções que decidem se uma rota pode ser ativada.
 */

/**
 * Guard de AUTENTICAÇÃO — "está logado?"
 *
 * Bloqueia rotas se o usuário não tem sessão ativa.
 * Redireciona para /login com `reason` e `returnUrl`.
 */
export { authGuard } from './guards/auth.guard';

/**
 * Guard de AUTORIZAÇÃO — "tem nível mínimo?"
 *
 * Bloqueia rotas se o nível do usuário for inferior ao exigido
 * pela rota (definido via `data.nivelMinimo`).
 */
export { nivelGuard } from './guards/nivel.guard';

/* ═══════════════════════════════════════════════════════════════════════
 * 3. UTILITÁRIOS DE HIERARQUIA DE NÍVEIS
 * ═══════════════════════════════════════════════════════════════════════
 * Funções puras usadas por guards, componentes e diretivas para
 * comparar níveis de acesso.
 */

/**
 * Hierarquia canônica dos níveis de acesso do EcoChatBot-Marcx.
 *
 * Ordem (do menor para o maior):
 *   atendente (0) < supervisor (1) < gerente (2) < administrador (3)
 */
export { NIVEIS_HIERARQUIA } from './niveis.auth';

/**
 * Retorna o índice numérico do nível na hierarquia.
 * Retorna -1 se o nível for desconhecido.
 */
export { ordemNivel } from './niveis.auth';

/**
 * Verifica se um nível atende ao mínimo exigido.
 * Retorna `true` se `minimo` for undefined (sem restrição).
 */
export { temNivelMinimo } from './niveis.auth';

/* ═══════════════════════════════════════════════════════════════════════
 * 4. MODELOS DA SESSÃO
 * ═══════════════════════════════════════════════════════════════════════
 * Tipos que descrevem o formato dos dados de sessão em memória.
 */

/**
 * Tipos exportados pelo modelo de sessão:
 *
 *   • SessionSnapshot  → fotografia imutável do estado da sessão
 *   • SessionStatus    → enum do status (anonymous, loading, authenticated, expired)
 *   • LoginCredentials → email + senha do formulário de login
 */
export type {
  SessionSnapshot,
  SessionStatus,
  LoginCredentials,
} from '/models/session.model';