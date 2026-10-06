/**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-MA · Core API
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     api-result.core.ts
@module   Core / API Result
@desc     Interface para resultados de requisições HTTP da API
@author   Aldemir Queiroz
@since    2026
@version  2.0.0  · ref: tipagem melhorada, documentação aprimorada
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 */

/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Tipo para resultados de requisições HTTP
 * Gerado automaticamente pelo openapi-typescript-codegen
 */
export type ApiResult = {
  /** URL da requisição original */
  readonly url: string;
  /** Indica se a requisição foi bem-sucedida (status 2xx) */
  readonly ok: boolean;
  /** Código HTTP da resposta */
  readonly status: number;
  /** Texto de status da resposta HTTP */
  readonly statusText: string;
  /** Corpo da resposta (pode ser qualquer tipo de dado) */
  readonly body: any;
};

/**
 * Interface para erros da API
 * Estende ApiResult para incluir informações de erro
 */
export interface ApiError extends ApiResult {
  /** Mensagem de erro detalhada */
  readonly message: string;
  /** Código de erro específico (opcional) */
  readonly code?: string;
  /** Detalhes adicionais do erro (opcional) */
  readonly details?: Record<string, unknown>;
}

export namespace ApiResult {
  export function isApiError(result: ApiResult): result is ApiError {
    return 'message' in result;
  }
}