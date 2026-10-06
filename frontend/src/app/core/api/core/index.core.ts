/**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-MA · Core API
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     index.core.ts
@module   Core / API Index
@desc     Ponto central de exportação para todos os módulos da API Core
@author   Aldemir Queiroz
@since    2026
@version  2.0.0  · ref: organização centralizada de exports
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 */

// Exporta tipos principais
export type { 
  ApiRequestOptions 
} from './api-request-options.core';

export type { 
  ApiResult 
} from './api-result.core';

export type { 
  OpenAPIConfig 
} from './open-api.core';

// Exporta utilitários do request.core
export { 
  isDefined,
  isString,
  isStringWithValue,
  isBlob,
  isFormData,
  base64,
  getQueryString,
  getFormData,
  resolve,
  getHeaders,
  getRequestBody,
  sendRequest,
  getResponseHeader,
  getResponseBody,
  toApiResult,
  toApiResultFromError,
  catchErrorCodes,
  request
} from './request.core';

// Exporta classes de erro
export { 
  ApiError 
} from './api-error.core';

// Exporta todos os módulos (para compatibilidade)
export * from './api-request-options.core';
export * from './api-result.core';
export * from './open-api.core';
export * from './request.core';
export * from './api-error.core';

// Exporta todos os módulos (para compatibilidade)
export * from './api-request-options.core';
export * from './api-result.core';
export * from './open-api.core';
export * from './request.core';
export * from './api-error.core';