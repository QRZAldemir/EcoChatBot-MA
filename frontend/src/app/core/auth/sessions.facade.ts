/**
 * ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 * EcoChatBot-MA · Sessions Facade
 * Codinome: EcoChatBot-MA
 * ───────────────────────────────────────────────────────────────────────────
 * @file     sessions.facade.ts
 * @module   Core / Auth / Facade
 * @author   Aldemir Queiroz
 * @since    2026
 * @version  1.0.0
 * ───────────────────────────────────────────────────────────────────────────
 *
 * FUNCIONALIDADE
 * ──────────────
 * Orquestrador central do CICLO DE VIDA DA SESSÃO do operador do bot.
 * É o ÚNICO ponto da aplicação que:
 *
 *   1. Autentica (login) via `AutenticacaoService` (codegen).
 *   2. Persiste o JWT + perfil via `TokenStorage`.
 *   3. Mantém o estado reativo (`session$`) para toda a UI.
 *   4. Implementa `SessionProvider` — contrato consumido por
 *      `createTokenResolver` para injetar o JWT em toda requisição.
 *   5. Encerra a sessão (logout) limpando estado + storage.
 *   6. Expõe `getToken()` SÍNCRONO — chamado a cada HTTP request.
 *
 * FLUXO DE INTEGRAÇÃO
 * ───────────────────
 *   LoginComponent
 *      └─→ SessionsFacade.login(credentials)
 *            └─→ AutenticacaoService.login()      [HTTP via núcleo puro]
 *            └─→ TokenStorage.setToken()          [persistência]
 *            └─→ this.session$.next(...)          [estado reativo]
 *
 *   request.core (antes de cada HTTP)
 *      └─→ token.resolver → SessionsFacade.getToken()   [leitura rápida]
 *
 *   ApiErrorInterceptor (401)
 *      └─→ SessionsFacade.invalidate()          [logout forçado]
 *
 * REGRAS DE DEPENDÊNCIA
 * ─────────────────────
 *   • PODE importar de `core/api` (AutenticacaoService, modelos).
 *   • PODE importar de `core/api/token.resolver` (SessionProvider).
 *   • NÃO deve importar HttpClient diretamente (codegen encapsula).
 *   • NÃO deve conter lógica de UI (toasts, redirects) — isso é do interceptor.
 *
 * ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 */

import { Injectable, inject } from '@angular/core';
import { BehaviorSubject, firstValueFrom, Observable } from 'rxjs';
import { map, tap } from 'rxjs/operators';

/* ─── Camada API (codegen) ───────────────────────────────────────────── */
import { AutenticacaoService }  from '../api/services/AutenticacaoService';
import type { LoginRequest }    from '../api/models/login-request.model';
import type { LoginResponse }   from '../api/models/login-response.model';
import type { UsuarioLogado }   from '../api/models/usuario-logado-models';

/* ─── Infra de transporte — contrato SessionProvider ─────────────────── */
import type { SessionProvider } from '../api/token.resolver';

/* ─── Internos da pasta auth ─────────────────────────────────────────── */
import { TokenStorage }         from './token.storage';
import type {
  SessionSnapshot,
  LoginCredentials,
} from './models/session.model';

/* ═══════════════════════════════════════════════════════════════════════
 * ESTADO INICIAL
 * ═══════════════════════════════════════════════════════════════════════
 * Snapshot usado antes de qualquer login e após qualquer logout.
 * Imutável por convenção — toda transição cria um novo objeto.
 */
const INITIAL_SNAPSHOT: SessionSnapshot = {
  status:    'anonymous',
  token:     null,
  user:      null,
  issuedAt:  null,
  expiresAt: null,
};

@Injectable({ providedIn: 'root' })
export class SessionsFacade implements SessionProvider {

  /* ═══════════════════════════════════════════════════════════════════
   * DEPENDÊNCIAS INJETADAS
   * ═══════════════════════════════════════════════════════════════════ */
  private readonly authApi = inject(AutenticacaoService);
  private readonly storage = inject(TokenStorage);

  /* ═══════════════════════════════════════════════════════════════════
   * ESTADO REATIVO (fonte de verdade em memória)
   * ═══════════════════════════════════════════════════════════════════ */
  private readonly state$ = new BehaviorSubject<SessionSnapshot>(INITIAL_SNAPSHOT);

  /** Stream público somente-leitura consumido pela UI. */
  readonly session$: Observable<SessionSnapshot> = this.state$.asObservable();

  /** Atalho reativo: `true` quando há sessão autenticada. */
  readonly isAuthenticated$ = this.session$.pipe(
    map(s => s.status === 'authenticated')
  );

  /** Atalho reativo: usuário logado (ou `null`). */
  readonly currentUser$ = this.session$.pipe(map(s => s.user));

  constructor() {
    /* Rehidrata a sessão a partir do storage ao subir a aplicação. */
    this.restoreFromStorage();
  }

  /* ═══════════════════════════════════════════════════════════════════
   * API PÚBLICA — CONSUMO PELA UI
   * ═══════════════════════════════════════════════════════════════════ */

  /**
   * Snapshot SÍNCRONO da sessão atual.
   * Útil para guards e para o `token.resolver` (que roda a cada HTTP).
   */
  get snapshot(): SessionSnapshot {
    return this.state$.value;
  }

  /**
   * Autentica o operador do bot.
   *
   * Em caso de sucesso:
   *   • persiste token + perfil no `TokenStorage`;
   *   • atualiza o estado reativo (`session$`);
   *   • retorna o snapshot final.
   *
   * Em caso de falha:
   *   • reverte o status para `'anonymous'`;
   *   • REPASSA o `ApiError` para o chamador — o `ApiErrorInterceptor`
   *     cuidará do toast / redirect.
   *
   * @throws ApiError (repassado do núcleo puro em falhas 4xx/5xx)
   */
  async login(credentials: LoginCredentials): Promise<SessionSnapshot> {
    /* 1. Marca estado de carregamento (UI mostra spinner) */
    this.patch({ status: 'loading' });

    /* 2. Monta payload no formato do codegen */
    const request: LoginRequest = {
         email: credentials.email,
         senha: credentials.senha,
    };

    try {
      /* 3. Dispara login via núcleo puro (request.core) */
      await firstValueFrom(
        this.authApi.loginApiAuthLoginPost(request).pipe(
          tap((res: LoginResponse) => this.persistSession(res))
        )
      );

      /* 4. Retorna snapshot final */
      return this.state$.value;
    } catch (err) {
      /* 5. Reverte estado — o erro segue para o interceptor */
      this.patch({ status: 'anonymous', token: null, user: null });
      throw err;
    }
  }

  /**
   * Encerra a sessão, limpa storage e redefine o estado.
   * Pode ser chamado manualmente (botão "Sair") ou pelo interceptor (401).
   */
  logout(): void {
    this.storage.clear();
    this.state$.next(INITIAL_SNAPSHOT);
  }

  /* ═══════════════════════════════════════════════════════════════════
   * IMPLEMENTAÇÃO DE SessionProvider
   * ═══════════════════════════════════════════════════════════════════
   * Estes 3 métodos são consumidos por `createTokenResolver` em
   * `core/api/token.resolver.ts`. NÃO ALTERAR ASSINATURAS.
   */

  /**
   * Retorna o JWT atual para injeção em `Authorization: Bearer`.
   * Método SÍNCRONO — chamado ANTES de cada requisição HTTP.
   *
   * @returns token ou `null` se não houver sessão
   */
  getToken(): string | null {
    return this.state$.value.token;
  }

  /**
   * Tenta renovar o token silenciosamente.
   *
   * @returns `null` — o backend atual do EcoChatBot-MA ainda não expõe
   *          endpoint `/auth/refresh`. Quando existir, implementar aqui:
   *
   *          const res = await firstValueFrom(this.authApi.refresh(...));
   *          return res.access_token;
   */
  async refresh(): Promise<string | null> {
    return null;
  }

  /**
   * Marca a sessão como inválida — chamado pelo resolver quando
   * não há token E não há como renovar.
   *
   * Delega para `logout()` para garantir limpeza total.
   */
  invalidate(): void {
    this.logout();
  }

  /* ═══════════════════════════════════════════════════════════════════
   * INTERNOS
   * ═══════════════════════════════════════════════════════════════════ */

  /**
   * Persiste a resposta de login e atualiza o snapshot reativo.
   * Normaliza campos com nomes variáveis vindos do backend
   * (`access_token` / `token` / `user` / `usuario`).
   */
  private persistSession(res: LoginResponse): void {
    /* Normalização tolerante — ajuste os nomes conforme a spec OpenAPI */
this.storage.setToken(res.access_token);
  this.storage.setUser(res.usuario);

  this.state$.next({
    status:    'authenticated',
    token:     res.access_token,
    user:      res.usuario,
    issuedAt:  Date.now(),
    expiresAt: null,
  });
  }

  /**
   * Rehidrata o estado a partir do `TokenStorage`.
   * Chamado no construtor — mantém o usuário logado após F5.
   */
  private restoreFromStorage(): void {
    const token = this.storage.getToken();
    const user  = this.storage.getUser<UsuarioLogado>();

    if (!token) {
      this.state$.next(INITIAL_SNAPSHOT);
      return;
    }

    this.state$.next({
      status:    'authenticated',
      token,
      user:      user ?? null,
      issuedAt:  null,
      expiresAt: null,
    });
  }

  /**
   * Atualiza parcialmente o snapshot — sempre criando um NOVO objeto
   * para respeitar a imutabilidade declarada no `SessionSnapshot`.
   */
  private patch(partial: Partial<SessionSnapshot>): void {
    this.state$.next({ ...this.state$.value, ...partial });
  }
}