/**
 * ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 * EcoChatBot-Marcx · API Extensions Module
 * Codinome: EcoChatBot-MA
 * ───────────────────────────────────────────────────────────────────────────
 * @file     api.extensions.module.ts
 * @module   Core / API / Extensions
 * @author   Aldemir Queiroz
 * @since    2026
 * @version  1.0.0
 * ───────────────────────────────────────────────────────────────────────────
 *
 * FUNCIONALIDADE
 * ──────────────
 * Complementa o NgModule OFICIAL gerado pelo codegen (`EcoChatApiClient`)
 * com providers que o codegen NÃO gera:
 *
 *   1. ApiErrorInterceptor → tratamento global de 401/403/5xx.
 *   2. BASE                → URL do backend via environment.
 *   3. TOKEN               → JWT dinâmico via SessionsFacade.
 *
 * ⚠️ POR QUE ESTE MÓDULO EXISTE
 * ────────────────────────────
 * O `openapi-typescript-codegen` regenera `ecochatclient.api.ts` a cada
 * mudança na spec OpenAPI, sobrescrevendo customizações. Para NÃO PERDER
 * as customizações, colocamos elas em um módulo SEPARADO.
 *
 * ORDEM DE IMPORTAÇÃO NO AppModule (CRÍTICO)
 * ──────────────────────────────────────────
 *   imports: [
 *     EcoChatApiClient,        // 1º — codegen (BASE, HttpClient, serviços)
 *     ApiExtensionsModule,     // 2º — custom (interceptor, token resolver)
 *   ]
 *
 * ⚠️ Se inverter a ordem, o codegen sobrescreve o TOKEN.
 *
 * ⚠️ ESCOPO MULTI-CANAL E MULTI-SEGMENTO
 * ─────────────────────────────────────
 * Este módulo é agnóstico de canal e segmento. Funciona igualmente em
 * WhatsApp, Telegram, Discord, Facebook, Instagram, PABX e em qualquer
 * segmento de negócio.
 *
 * QUEM GERA
 * ─────────
 * Arquivo CUSTOM (não é gerado pelo codegen).
 *
 * QUEM CONSOME
 * ────────────
 *   • AppModule               → importa este módulo
 *   • AppConfig (standalone)  → usa ECOCHAT_API_PROVIDERS equivalentes
 *
 * ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 */

import { NgModule, inject } from '@angular/core';
import { HTTP_INTERCEPTORS } from '@angular/common/http';

import { ApiErrorInterceptor } from './api-error.interceptor';
import { createTokenResolver } from './token.resolver';
import { OpenAPI } from './core/index.core';
import { SessionsFacade } from '../auth/sessions.facade';
import { environment } from 'src/environments/environment';

@NgModule({
  providers: [
    /* ═════════════════════════════════════════════════════════════════
     * 1. INTERCEPTOR GLOBAL DE ERROS
     * ═════════════════════════════════════════════════════════════════
     * Captura toda resposta HTTP que falhe e aplica a política central:
     *   401 → logout + redirect /login
     *   403 → toast "permissão negada"
     *   5xx → toast "serviço indisponível" + telemetria
     *
     * `multi: true` permite coexistir com outros interceptores.
     */
    {
      provide: HTTP_INTERCEPTORS,
      useClass: ApiErrorInterceptor,
      multi: true,
    },

    /* ═════════════════════════════════════════════════════════════════
     * 2. CONFIGURAÇÃO DO OpenAPI + TOKEN DINÂMICO
     * ═════════════════════════════════════════════════════════════════
     * Sobrescreve APENAS os campos BASE e TOKEN, preservando VERSION,
     * HEADERS, ENCODE_PATH etc. definidos pelo codegen.
     */
    {
      provide: OpenAPI,
      useFactory: () => {
        const session = inject(SessionsFacade);
        return {
          ...OpenAPI,
          BASE: environment.apiUrl,
          TOKEN: createTokenResolver(session),
        };
      },
    },
  ],
})
export class ApiExtensionsModule { }