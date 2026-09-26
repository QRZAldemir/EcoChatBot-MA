/**
 * ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 * EcoChatBot-MA · Token Storage
 * Codinome: EcoChatBot-MA
 * ───────────────────────────────────────────────────────────────────────────
 * @file     token.storage.ts
 * @module   Core / Auth / Persistence
 * @author   Aldemir Queiroz
 * @since    2026
 * @version  1.0.0
 * ───────────────────────────────────────────────────────────────────────────
 *
 * FUNCIONALIDADE
 * ──────────────
 * Serviço que ABSTRAI a persistência do JWT e do perfil do operador
 * no navegador.
 *
 * Isola a `SessionsFacade` (e qualquer outro consumidor) de QUALQUER
 * decisão sobre ONDE os dados são guardados. Trocar localStorage por
 * sessionStorage, IndexedDB, cookie ou memória pura é uma questão de
 * reescrever APENAS esta classe.
 *
 * ⚠️ RESPONSABILIDADE ÚNICA
 * ─────────────────────────
 * Esta classe NÃO:
 *   • Chama HTTP (isso é `core/api/services/`)
 *   • Valida JWT (isso é responsabilidade do backend)
 *   • Gerencia estado reativo (isso é `SessionsFacade`)
 *   • Decide política de expiração
 *
 * Esta classe SÓ:
 *   • Lê / escreve / remove strings no localStorage
 *   • Serializa / desserializa objetos (JSON)
 *   • Fornece uma API tipada para os consumidores
 *
 * ⚠️ SEGURANÇA — LEIA COM ATENÇÃO
 * ───────────────────────────────
 * localStorage é acessível por QUALQUER script da página (risco XSS).
 * Um atacante que consiga injetar JavaScript pode ler o token e se
 * passar pelo operador.
 *
 * RECOMENDAÇÕES PARA PRODUÇÃO:
 *   • Prefira httpOnly cookie + BFF (Backend For Frontend).
 *   • Se usar localStorage, sempre use HTTPS.
 *   • Configure Content-Security-Policy (CSP) restritivo.
 *   • Implemente rotação de tokens.
 *   • Monitore vazamentos (ex.: Sentry, logging de erros).
 *
 * ESTA IMPLEMENTAÇÃO SERVE PARA:
 *   • Desenvolvimento local
 *   • Protótipos
 *   • Ambientes internos (rede fechada)
 *
 * ⚠️ ESCOPO MULTI-CANAL E MULTI-SEGMENTO
 * ─────────────────────────────────────
 * Esta classe é agnóstica de canal e segmento. Funciona igualmente
 * em WhatsApp, Telegram, Discord, Facebook, Instagram, PABX e em
 * qualquer segmento de negócio (saúde, financeiro, varejo, educação,
 * jurídico, turismo, governo, serviços).
 *
 * ESTRUTURA DOS DADOS PERSISTIDOS
 * ───────────────────────────────
 *   localStorage
 *   ├── ecochatbot_ma.token   → string JWT
 *   └── ecochatbot_ma.user    → JSON do UsuarioLogado
 *
 * FLUXO DE USO
 * ────────────
 *   SessionsFacade
 *     ├─→ login()  → storage.setToken(jwt) + storage.setUser(usuario)
 *     ├─→ logout() → storage.clear()
 *     ├─→ restore  → storage.getToken() + storage.getUser()
 *     └─→ getToken → storage.getToken()
 *
 * QUEM GERA
 * ─────────
 * Arquivo CUSTOM (não é gerado pelo codegen).
 *
 * QUEM CONSOME
 * ────────────
 *   • SessionsFacade          → orquestrador principal
 *   • Testes unitários        → para mockar persistência
 *   • Futuros serviços de auth → se houver
 *
 * ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 */

import { Injectable } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class TokenStorage {

  /* ═══════════════════════════════════════════════════════════════════════
   * CONSTANTES PRIVADAS
   * ═══════════════════════════════════════════════════════════════════════
   * As chaves de armazenamento são privadas para evitar colisões com
   * outras aplicações que possam rodar no mesmo domínio (ex.: painel
   * administrativo e site institucional).
   */

  /**
   * Chave usada para armazenar o JWT no localStorage.
   *
   * Prefixo `ecochatbot_ma.` para evitar colisão com outras aplicações
   * no mesmo domínio.
   */
  private static readonly TOKEN_KEY = 'ecochatbot_ma.token';

  /**
   * Chave usada para armazenar o perfil do operador no localStorage.
   */
  private static readonly USER_KEY = 'ecochatbot_ma.user';

  /* ═══════════════════════════════════════════════════════════════════════
   * TOKEN — JWT
   * ═══════════════════════════════════════════════════════════════════════
   * Métodos para ler, gravar e remover o JWT.
   */

  /**
   * Retorna o JWT armazenado (ou `null` se não houver sessão).
   *
   * Uso:
   *   • `SessionsFacade.restoreFromStorage()` no bootstrap da app
   *   • `token.resolver` a cada requisição HTTP (via SessionsFacade)
   *
   * @returns string do JWT ou `null`
   */
  getToken(): string | null {
    return localStorage.getItem(TokenStorage.TOKEN_KEY);
  }

  /**
   * Persiste o JWT no localStorage.
   *
   * Chamado após login bem-sucedido pela `SessionsFacade`.
   *
   * ⚠️ Só é chamado quando o backend retorna `access_token` válido.
   *
   * @param token string do JWT (nunca vazio)
   */
  setToken(token: string): void {
    localStorage.setItem(TokenStorage.TOKEN_KEY, token);
  }

  /**
   * Remove APENAS o JWT do localStorage.
   *
   * ⚠️ Use `clear()` para remover token E perfil de uma vez.
   * Use `clearToken()` apenas em cenários específicos (ex.: refresh).
   */
  clearToken(): void {
    localStorage.removeItem(TokenStorage.TOKEN_KEY);
  }

  /* ═══════════════════════════════════════════════════════════════════════
   * PERFIL DO USUÁRIO
   * ═══════════════════════════════════════════════════════════════════════
   * Métodos para ler, gravar e remover o perfil do operador.
   */

  /**
   * Retorna o perfil do operador armazenado (ou `null` se não houver).
   *
   * O tipo é genérico (`T`) para permitir que o chamador escolha o
   * tipo do perfil (ex.: `UsuarioLogado`).
   *
   * ⚠️ Retorna `null` se:
   *   • Não há dado no localStorage
   *   • O JSON está corrompido (try/catch interno)
   *
   * @template T tipo do perfil
   * @returns objeto do perfil ou `null`
   */
  getUser<T = unknown>(): T | null {
    const raw = localStorage.getItem(TokenStorage.USER_KEY);
    if (!raw) return null;

    try {
      return JSON.parse(raw) as T;
    } catch {
      /* JSON corrompido — limpa e retorna null */
      this.clearUser();
      return null;
    }
  }

  /**
   * Persiste o perfil do operador no localStorage.
   *
   * Chamado após login bem-sucedido pela `SessionsFacade`.
   *
   * @param user objeto do perfil (será serializado em JSON)
   */
  setUser(user: unknown): void {
    localStorage.setItem(TokenStorage.USER_KEY, JSON.stringify(user));
  }

  /**
   * Remove APENAS o perfil do localStorage.
   *
   * ⚠️ Use `clear()` para remover token E perfil de uma vez.
   */
  clearUser(): void {
    localStorage.removeItem(TokenStorage.USER_KEY);
  }

  /* ═══════════════════════════════════════════════════════════════════════
   * LIMPEZA TOTAL
   * ═══════════════════════════════════════════════════════════════════════
   * Método usado no logout para limpar toda a sessão.
   */

  /**
   * Remove TODOS os dados de sessão do localStorage.
   *
   * Chamado por:
   *   • `SessionsFacade.logout()` — logout voluntário
   *   • `SessionsFacade.invalidate()` — logout forçado (401)
   *   • `ApiErrorInterceptor` — ao detectar token expirado
   *
   * ⚠️ Este é o método PADRÃO para encerrar sessão.
   * Use `clearToken()` ou `clearUser()` apenas em cenários específicos.
   */
  clear(): void {
    this.clearToken();
    this.clearUser();
  }

  /* ═══════════════════════════════════════════════════════════════════════
   * HELPERS (utilitários internos)
   * ═══════════════════════════════════════════════════════════════════════
   * Métodos auxiliares usados internamente ou por consumidores avançados.
   */

  /**
   * Verifica se há uma sessão persistida.
   *
   * Útil para decisões rápidas em guards, antes de buscar o perfil
   * completo (que exige parsing de JSON).
   *
   * @returns `true` se existe um JWT válido armazenado
   */
  hasSession(): boolean {
    return !!this.getToken();
  }

  /**
   * Verifica se há um JWT E um perfil persistidos.
   *
   * Diferente de `hasSession()`, este método exige que ambos os dados
   * estejam presentes. Útil para restaurar sessão após F5.
   *
   * @returns `true` se token E perfil existem
   */
  hasFullSession(): boolean {
    return !!this.getToken() && !!this.getUser();
  }
}