/**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-MA · Core API
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     api-request-options.core.ts
@module   Core / API Options
@desc     Interface de opções para requisições HTTP da API
@author   Aldemir Queiroz
@since    2026
@version  2.0.0  · ref: adição de mediaType, melhor tipagem
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 */

/**
 * Interface para opções de requisição HTTP
 */
export interface ApiRequestOptions {
  /** Método HTTP (GET, POST, PUT, etc.) */
  method: string;

  /** URL da requisição */
  url: string;

  /** Headers HTTP */
  headers?: Record<string, string>;

  /** Parâmetros de URL */
  params?: Record<string, unknown>;

  /** Corpo da requisição */
  body?: unknown;

  /** Tipo de mídia para o corpo da requisição */
  mediaType?: string;

  /** Tipo de resposta esperada */
  responseType?: string;

  /** Parâmetros de path para substituição na URL */
  path?: Record<string, string>;

  /** Parâmetros de query para adicionar à URL */
  query?: Record<string, unknown>;

  /** Dados do formulário */
  formData?: Record<string, unknown>;
}
