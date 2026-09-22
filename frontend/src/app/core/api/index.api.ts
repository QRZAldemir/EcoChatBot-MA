/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 * EcoChatBot-Marcx · API Barrel (ponto de entrada público)
 * Codinome: EcoChatBot-MA
 * ───────────────────────────────────────────────────────────────────────────
 * @file     index.api.ts
 * @module   Core / API / Public API
 * @author   Aldemir Queiroz
 * @since    2026
 * @version  1.1.0  · add: 6 linhas de export (AngularHttpRequest + interceptor + resolver)
 * ───────────────────────────────────────────────────────────────────────────
 *
 * FUNCIONALIDADE
 * ──────────────
 * Barrel público da camada `core/api/`. Centraliza TODOS os exports da
 * camada de comunicação do EcoChatBot-Marcx, permitindo que features
 * importem tudo com um caminho único:
 *
 *   import { MensagensService, ApiError } from '@core/api';
 *
 * ⚠️ ARQUIVO GERADO — ao rodar `codegen`, preserve o bloco "🆕 EXTRAS"
 * que fica logo após os exports do núcleo puro.
 *
 * ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 */

/* ─── 1. Cliente Angular (NgModule) ──────────────────────────────────── */
export { EcoChatApiClient } from './ecochatclient.api';

/* ─── 2. Núcleo puro — contratos, erros, configuração ────────────────── */
export { ApiError }                        from './core/api-error.core';
export { BaseHttpRequest }                 from './core/base-http-request.core';
export { CancelablePromise, CancelError }  from './core/cancelable-promise.core';
export { OpenAPI }                         from './core/open-api.core';
export type { OpenAPIConfig }              from './core/open-api.core';

/* ────────────────────────────────────────────────────────────────────────
 * 🆕 EXTRAS — adicionado por Aldemir Queiroz (6 linhas)
 * ──────────────────────────────────────────────────────────────────────── */

/* 3. Contratos públicos do núcleo */
export type { ApiRequestOptions }          from './core/api-request-options.core';
export type { ApiResult }                  from './core/api-result.core';

/* 4. Implementação concreta do transporte */
export { AngularHttpRequest }              from './core/angular-http-request.core';

/* 5. Integração Angular — interceptor + resolver */
export { ApiErrorInterceptor }             from './api-error.interceptor';
export type { ToastService }               from './api-error.interceptor';
export {
  createTokenResolver,
  LocalStorageSessionProvider,
}                                          from './token.resolver';
export type { SessionProvider }            from './token.resolver';

/* ────────────────────────────────────────────────────────────────────────
 * FIM DOS EXTRAS
 * ──────────────────────────────────────────────────────────────────────── */

/* ─── 6. Modelos de domínio (gerados pelo codegen) ───────────────────── */
export type { CanalCreate }                from './models/canal-create.models';
export type { CanalResponse }              from './models/canal-response.models';
export type { CanalUpdate }                from './models/canal-update.models';
export type { ConversaRequest }            from './models/conversa-request.model';
export type { CriarAlteraContextRequest }  from './models/criar-altera-context-request.models';
export type { DeletarContextRequest }      from './models/deletar-context-request.models';
export type { DepartamentoCreate }         from './models/departamento-create.models';
export type { DepartamentoResponse }       from './models/departamento-response.models';
export type { DepartamentoUpdate }         from './models/departamento-update.models';
export type { EncerrarAtendimentoRequest } from './models/encerrar-atendimento-request.models';
export type { EnviarMensagemRequest }      from './models/envia-mensagem-request.model';
export type { EnviarTemplateRequest }      from './models/envia-template-request.models';
export type { GerarAudioRequest }          from './models/gera-audio-resquest.models';
export type { GerarAudioResponse }         from './models/gera-audio-response.models';
export type { HTTPValidationError }        from './models/http-validation-error.models';
export type { LoginRequest }               from './models/login-request.model';
export type { LoginResponse }              from './models/login-response.model';
export type { MensagemIA }                 from './models/mensagem-ia.models';
export type { MensagemItem }               from './models/mensagem-item.models';
export type { MenuCreate }                 from './models/menu-create.models';
export type { MenuEnviarRequest }          from './models/menu-envia-request.models';
export type { MenuOpcaoCreate }            from './models/menu-opcao-create.models';
export type { MenuOpcaoResponse }          from './models/menu-opcao-response.models';
export type { MenuOpcaoUpdate }            from './models/menu-opcao-update.models';
export type { MenuResponse }               from './models/menu-response.models';
export type { MenuUpdate }                 from './models/menu-update.models';
export type { ModeloMensagemCreate }       from './models/mensagem-create.models';
export type { ModeloMensagemResponse }     from './models/mensagem-response.models';
export type { ModeloMensagemUpdate }       from './models/mensagem-update.models';
export type { NivelUsuarioResponse }       from './models/nivel-usuario-response.models';
export type { OpcaoRequest }               from './models/opcao-request.models';
export type { RespostaIA }                 from './models/resposta-ia.models';
export type { TemplateParametro }          from './models/template-parametros.models';
export type { TransferirAtendimentoRequest } from './models/transferir-atendimento-request.models';
export type { UsuarioCreate }              from './models/usuario-creator.models';
export type { UsuarioListItem }            from './models/usuario-listaitens-models';
export type { UsuarioLogado }              from './models/usuario-logado-models';
export type { UsuarioResponse }            from './models/usuario_response.model';
export type { UsuarioUpdate }              from './models/usuario_update.models';
export type { ValidationError }            from './models/valida-erros.models';
export type { VerificarMensagemRequest }   from './models/verifica-mensagem-request.models';

/* ─── 7. Serviços de domínio (gerados pelo codegen) ──────────────────── */
export { AtendimentoService }              from './services/AtendimentoService';
export { AudioService }                    from './services/AudioService';
export { AutenticacaoService }             from './services/AutenticacaoService';
export { CanaisService }                   from './services/CanaisService';
export { DepartamentosService }            from './services/DepartamentosService';
export { InteligenciaArtificialService }   from './services/InteligenciaArtificialService';
export { MensagensService }                from './services/MensagensService';
export { MenusService }                    from './services/MenusService';
export { ModelosDeMensagemService }        from './services/ModelosDeMensagemService';
export { MonitoramentoService }            from './services/MonitoramentoService';
export { RootService }                     from './services/RootService';
export { UsuariosService }                 from './services/usuarioservice';
export { WebhookService }                  from './services/WebhookService';