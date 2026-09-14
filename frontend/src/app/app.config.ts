// ============================================================================
// CONFIGURAÇÃO GLOBAL DA APLICAÇÃO (Angular 17 — Standalone)
// ============================================================================
//
// @file    app.config.ts
// @author  Aldemir Queiroz
// @since   2024
// @angular 17.x
// @pattern Standalone ApplicationConfig + provideHttpClient(withInterceptors)
//
// ----------------------------------------------------------------------------
// O QUE É ESTE ARQUIVO?
// ----------------------------------------------------------------------------
// É o arquivo de configuração global da aplicação standalone (Angular 17+).
// Ele SUBSTITUI o antigo `AppModule` da arquitetura antiga (NgModule).
//
// Aqui registramos "serviços globais" (providers) que estarão disponíveis
// para injeção de dependência em TODA a aplicação:
//   - Router (navegação)
//   - HttpClient (chamadas HTTP) + interceptors
//   - Otimizações de change detection (performance)
//
// É consumido pelo `main.ts` no bootstrap:
//   bootstrapApplication(AppComponent, appConfig)
// ============================================================================

// ----------------------------------------------------------------------------
// IMPORTS
// ----------------------------------------------------------------------------
import {
  ApplicationConfig,             // Tipo do objeto de configuração da aplicação
  provideZoneChangeDetection,    // Provider de otimização da detecção de mudanças
} from '@angular/core';

import { provideRouter } from '@angular/router';
// ↑ Habilita o roteamento no modo standalone (substitui RouterModule.forRoot).

import {
  provideHttpClient,   // Torna o HttpClient injetável em toda a aplicação
  withInterceptors,    // Feature que REGISTRA interceptors funcionais (Angular 15+)
} from '@angular/common/http';
// ↑ ATENÇÃO: `withInterceptors` PRECISA ser importado do mesmo pacote
//   que `provideHttpClient`. Se importar só o provideHttpClient e tentar usar
//   withInterceptors, dá erro TS2304 ("Cannot find name 'withInterceptors'").

import { routes } from './app.routes';
// ↑ Array de rotas definido em app.routes.ts.

import { httpInterceptor } from './core/models/interceptors/http.interceptor';
// ↑ ✅ NOME CORRETO do export.
//   ❌ Antes estava `authInterceptor` — gerava erro TS2724:
//      "has no exported member named 'authInterceptor'.
//       Did you mean 'httpInterceptor'?"
//
//   ⚠️ CAMINHO CORRETO: `core/interceptors/` (não `core/models/interceptors/`).
//      Interceptors NÃO são models — models são tipos/interfaces de domínio.

// ----------------------------------------------------------------------------
// CONFIGURAÇÃO DA APLICAÇÃO
// ----------------------------------------------------------------------------
/**
 * Objeto de configuração global.
 * Tudo que está em `providers` fica disponível para injeção em qualquer
 * componente/serviço da aplicação (injetor raiz).
 */
export const appConfig: ApplicationConfig = {
  providers: [
    // ----------------------------------------------------------------------
    // 1) OTIMIZAÇÃO DE CHANGE DETECTION
    // ----------------------------------------------------------------------
    // `eventCoalescing: true` agrupa múltiplos eventos disparados no mesmo
    // tick em um único ciclo de detecção de mudanças.
    //
    // BENEFÍCIO: menos ciclos de CD → aplicação mais fluida, especialmente
    // em listas grandes ou formulários com muitos eventos (input, click...).
    //
    // `provideZoneChangeDetection` é o novo jeito de configurar isso no
    // Angular standalone (antes era `NgZone` no AppModule).
    provideZoneChangeDetection({ eventCoalescing: true }),

    // ----------------------------------------------------------------------
    // 2) ROTEAMENTO
    // ----------------------------------------------------------------------
    // Registra as rotas da aplicação.
    // Equivalente ao antigo `RouterModule.forRoot(routes)` do NgModule.
    provideRouter(routes),

    // ----------------------------------------------------------------------
    // 3) HTTP CLIENT + INTERCEPTORS
    // ----------------------------------------------------------------------
    // `provideHttpClient()` → disponibiliza o HttpClient para injeção.
    //
    // Por padrão, já vem com proteção XSRF habilitada para requisições
    // que modificam estado (POST/PUT/DELETE).
    //
    // Recursos adicionais são ativados via "features" (funções auxiliares):
    //   - withInterceptors([...])         → interceptors funcionais (Angular 17)
    //   - withInterceptorsFromDi()        → interceptors em classe (legado)
    //   - withFetch()                     → usa Fetch API (recomendado em SSR)
    //   - withXsrfConfiguration(...)      → customiza proteção XSRF
    //   - withNoXsrfProtection()          → desabilita proteção XSRF
    //   - withJsonpSupport()              → habilita suporte a JSONP
    //   - withRequestsMadeViaParent()     → permite interceptors do parent
    //
    // AQUI: usamos `withInterceptors([httpInterceptor])` para registrar
    // nosso interceptor funcional que cuida de auth + tratamento de erros.
    provideHttpClient(
      // Array de interceptors funcionais.
      // ORDEM IMPORTA: o primeiro intercepta a IDA primeiro e a VOLTA por
      // último. Aqui só temos um, então a ordem é irrelevante — mas em
      // aplicações com vários, defina da camada mais externa para a mais interna.
      withInterceptors([httpInterceptor]),
    ),

    // 💡 DICA SSR: se a aplicação usa Server-Side Rendering, adicione
    //    `withFetch()` para melhor performance e compatibilidade:
    //
    //    provideHttpClient(
    //      withInterceptors([httpInterceptor]),
    //      withFetch(),
    //    ),
  ],
};