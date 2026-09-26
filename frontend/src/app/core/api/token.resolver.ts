/**
 * ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 * EcoChatBot-MA · Token Resolver
 * Codinome: EcoChatBot-MA
 * ───────────────────────────────────────────────────────────────────────────
 * @file     token.resolver.ts
 * @module   Core / API / Authentication
 * @author   Aldemir Queiroz
 * @since    2026
 * @version  1.0.0
 * ───────────────────────────────────────────────────────────────────────────
 *
 * FUNCIONALIDADE
 * ──────────────
 * Fábrica que fornece o `Resolver<string>` consumido pelo campo `TOKEN`
 * da configuração `OpenAPIConfig`.
 *
 * O núcleo puro (`request.core.ts`) chama esse resolver IMEDIATAMENTE
 * ANTES de cada requisição HTTP — o que garante que o JWT esteja sempre
 * atualizado no momento exato do envio.
 *
 * ⚠️ DIFERENÇA ENTRE TOKEN ESTÁTICO E DINÂMICO
 * ───────────────────────────────────────────
 *   Token ESTÁTICO:
 *     TOKEN: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
 *     → Envelhece. Exige reload da página para atualizar.
 *
 *   Token DINÂMICO (este arquivo):
 *     TOKEN: createTokenResolver(session)
 *     → Sempre fresco. Refresh silencioso quando expira.
 *
 * O QUE O RESOLVER FAZ
 * ────────────────────
 *   1. Tenta ler o token atual da sessão (rápido).
 *   2. Se vazio e houver `refresh()`, tenta renovar.
 *   3. Se ainda vazio, invalida a sessão (`invalidate()`).
 *   4. Retorna string vazia → requisição anônima.
 *
 * O QUE O RESOLVER NÃO FAZ
 * ────────────────────────
 *   • NÃO redireciona para login (isso é do `ApiErrorInterceptor`)
 *   • NÃO exibe toasts de erro (isso é do interceptor)
 *   • NÃO decide política de logout (isso é da facade)
 *   • NÃO faz chamadas HTTP (o refresh é delegado à facade)
 *
 * ⚠️ ESCOPO MULTI-CANAL E MULTI-SEGMENTO
 * ─────────────────────────────────────
 * Este resolver é agnóstico de canal e segmento. Funciona igualmente
 * em WhatsApp, Telegram, Discord, Facebook, Instagram, PABX e em
 * qualquer segmento de negócio.
 *
 * CONTRATO `SessionProvider`
 * ──────────────────────────
 * Interface mínima que qualquer `AuthService` ou `SessionsFacade`
 * deve implementar para plugar neste resolver:
 *
 *   interface SessionProvider {
 *     getToken(): string | null;
 *     refresh?(): Promise<string | null>;
 *     invalidate?(): void;
 *   }
 *
 * FLUXO DE INTEGRAÇÃO
 * ───────────────────
 *   ┌─────────────────────────────────────────────────────────────────┐
 *   │  ApiExtensionsModule (bootstrap)                                │
 *   │    └─→ { provide: OpenAPI, useFactory: () => ({                 │
 *   │           ...OpenAPI,                                           │
 *   │           TOKEN: createTokenResolver(inject(SessionsFacade))    │
 *   │         })}                                                     │
 *   └─────────────────────────────────────────────────────────────────┘
 *                              ↓
 *   ┌─────────────────────────────────────────────────────────────────┐
 *   │  request.core (a cada requisição HTTP)                          │
 *   │    └─→ const token = await resolve(options, config.TOKEN)       │
 *   │    └─→ headers['Authorization'] = `Bearer ${token}`             │
 *   └─────────────────────────────────────────────────────────────────┘
 *
 * QUEM GERA
 * ─────────
 * Arquivo CUSTOM (não é gerado pelo codegen).
 *
 * QUEM CONSOME
 * ────────────
 *   • api.extensions.module.ts → registra o resolver no provider OpenAPI
 *
 * ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 */

import type { ApiRequestOptions } from './core/index.core';

/* ═══════════════════════════════════════════════════════════════════════
 * CONTRATO `SessionProvider`
 * ═══════════════════════════════════════════════════════════════════════
 * Interface mínima que qualquer serviço de sessão deve implementar.
 */

/**
 * Contrato mínimo esperado de um provedor de sessão do EcoChatBot-MA.
 *
 * Implemente este contrato no seu `AuthService` / `SessionsFacade`.
 *
 * @example
 * ```typescript
 * @Injectable({ providedIn: 'root' })
 * export class SessionsFacade implements SessionProvider {
 *   getToken()    { return this.state$.value.token; }
 *   async refresh() { return null; }  // quando o backend expor
 *   invalidate()  { this.logout(); }
 * }
 * ```
 */
export interface SessionProvider {

  /**
   * Retorna o token atual.
   *
   * @returns string do JWT ou `null` se não houver sessão
   */
  getToken(): string | null;

  /**
   * Tenta renovar o token silenciosamente.
   *
   * Retorne `null` se a renovação falhar — o resolver vai
   * chamar `invalidate()`.
   *
   * ⚠️ Opcional — se não implementado, o resolver não tenta refresh.
   */
  refresh?(): Promise<string | null>;

  /**
   * Marca a sessão como inválida (logout forçado, token irrecuperável).
   *
   * ⚠️ Opcional — se não implementado, o resolver só retorna string vazia.
   */
  invalidate?(): void;
}

/* ═══════════════════════════════════════════════════════════════════════
 * FÁBRICA DO RESOLVER
 * ═══════════════════════════════════════════════════════════════════════
 * Função que cria o resolver consumido pelo OpenAPIConfig.TOKEN.
 */

/**
 * Cria um resolver compatível com `OpenAPIConfig.TOKEN`.
 *
 * O resolver retorna uma `Promise<string>` que será aguardada pelo
 * núcleo puro antes de cada requisição HTTP.
 *
 * Fluxo interno:
 *   1. Tenta `session.getToken()` — caminho rápido.
 *   2. Se vazio e houver `refresh()`, tenta `session.refresh()`.
 *   3. Se ainda vazio, chama `session.invalidate?.()`.
 *   4. Retorna `''` — requisição anônima.
 *
 * @param session Provedor de sessão (SessionsFacade, AuthService, etc.)
 * @returns Função async que resolve o token a cada request
 *
 * @example
 * ```typescript
 * // Em api.extensions.module.ts:
 * const tokenResolver = createTokenResolver(inject(SessionsFacade));
 *
 * export const ECOCHAT_API_CONFIG: OpenAPIConfig = {
 *   ...OpenAPI,
 *   BASE:  environment.apiUrl,
 *   TOKEN: tokenResolver,
 * };
 * ```
 */
export function createTokenResolver(session: SessionProvider) {

  /**
   * Resolve o token JWT para a próxima requisição HTTP.
   *
   * @param _options Opções da requisição (não usadas — reservadas)
   * @returns Token JWT ou `''` para requisição anônima
   */
  return async (_options: ApiRequestOptions): Promise<string> => {

    /* ─────────────────────────────────────────────────────────────────
     * 1. CAMINHO RÁPIDO — token em memória
     * ─────────────────────────────────────────────────────────────────
     * Se a sessão está ativa, o token já está em memória (o snapshot
     * do SessionsFacade). Retorna imediatamente.
     */
    const current = session.getToken();
    if (current) return current;

    /* ─────────────────────────────────────────────────────────────────
     * 2. TENTATIVA DE REFRESH — se disponível
     * ─────────────────────────────────────────────────────────────────
     * Se o token expirou e a sessão implementou `refresh()`, tenta
     * renovar silenciosamente antes de desistir.
     */
    if (session.refresh) {
      const refreshed = await session.refresh();
      if (refreshed) return refreshed;
    }

    /* ─────────────────────────────────────────────────────────────────
     * 3. INVALIDAÇÃO — sessão irrecuperável
     * ─────────────────────────────────────────────────────────────────
     * Sem token e sem refresh → a sessão está morta. Notifica a
     * facade para que ela faça a limpeza (remover do storage,
     * emitir session$ com status 'anonymous').
     */
    session.invalidate?.();

    /* ─────────────────────────────────────────────────────────────────
     * 4. REQUISIÇÃO ANÔNIMA
     * ─────────────────────────────────────────────────────────────────
     * Retorna string vazia. O núcleo puro NÃO adiciona o header
     * `Authorization` quando o token é vazio (ver `getHeaders` em
     * `request.core.ts`).
     *
     * O backend, se exigir autenticação, responderá 401. O
     * `ApiErrorInterceptor` tratará o 401 (logout + redirect).
     */
    return '';
  };
}