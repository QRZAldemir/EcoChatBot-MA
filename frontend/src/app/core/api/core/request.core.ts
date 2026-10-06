/**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-MA · Core API
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     request.core.ts
@module   Core / Transport Pipeline
@desc     Pipeline central de TODAS as requisições HTTP do EcoChatBot.
          Responsabilidades:
            1. Montar URL (path params + query string).
            2. Resolver headers (auth token/basic + content-type).
            3. Serializar body / form-data (ex.: upload de anexos do bot).
            4. Enviar via Angular HttpClient (observe: 'response').
            5. Normalizar resposta para `ApiResult`.
            6. Mapear códigos HTTP de erro para `ApiError'.
@author   Aldemir Queiroz
@since    2026
@version  2.0.0  · ref: pipeline RxJS otimizado, type guards corrigidos
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 */

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 1. IMPORTAÇÕES
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
import {
  HttpClient,
  HttpHeaders,
  HttpResponse,
  HttpErrorResponse
} from '@angular/common/http';

import {
  forkJoin,
  of,
  throwError,
  Observable
} from 'rxjs';

import {
  catchError,
  map,
  switchMap
} from 'rxjs/operators';

import { ApiError } from './api-error.core';
import type { ApiRequestOptions } from './api-request-options.core';
import type { ApiResult } from './api-result.core';
import type { OpenAPIConfig } from './open-api.core';

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 2. TYPE GUARDS
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
/**
 * Verifica se um valor está definido (não é null nem undefined)
 */
export const isDefined = <T>(value: T | null | undefined): value is Exclude<T, null | undefined> =>
  value !== undefined && value !== null;

/**
 * Verifica se um valor é uma string
 */
export const isString = (value: unknown): value is string =>
  typeof value === 'string';

/**
 * Verifica se um valor é uma string não vazia
 */
export const isStringWithValue = (value: unknown): value is string =>
  isString(value) && value !== '';

/**
 * Verifica se um valor é um Blob
 */
export const isBlob = (value: unknown): value is Blob => {
  return (
    typeof value === 'object' &&
    typeof (value as Blob).type === 'string' &&
    typeof (value as Blob).stream === 'function' &&
    typeof (value as Blob).arrayBuffer === 'function' &&
    typeof (value as Blob).constructor === 'function' &&
    typeof (value as Blob).constructor.name === 'string' &&
    /^(Blob|File)$/.test((value as Blob).constructor.name) );
};

/**
 * Verifica se um valor é um FormData
 */
export const isFormData = (value: unknown): value is FormData =>
  value instanceof FormData;

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 3. HELPERS
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
/**
 * Converte uma string para base64
 */
export const base64 = (str: string): string => {
  try {
    return btoa(str);
  } catch {
    // @ts-ignore — fallback Node
    return Buffer.from(str).toString('base64');
  }
};

/**
 * Gera uma string de query parameters a partir de um objeto
 */
export const getQueryString = (params: Record<string, unknown>): string => {
  const qs: string[] = [];
  
  const append = (key: string, value: unknown) => {
    qs.push(`${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`);
  };

  const process = (key: string, value: unknown): void => {
    if (!isDefined(value)) return;
    if (Array.isArray(value)) {
      value.forEach(v => process(key, v));
    } else if (typeof value === 'object' && value !== null) {
      Object.entries(value).forEach(([k, v]) => process(`${key}[${k}]`, v));
    } else {
      append(key, value);
    }
  };

  Object.entries(params).forEach(([key, value]) => process(key, value));
  return qs.length ? `?${qs.join('&')}` : '';
};

/**
 * Monta a URL completa com base na configuração e opções da requisição
 */
const getUrl = (config: OpenAPIConfig, options: ApiRequestOptions): string => {
  const encoder = config.ENCODE_PATH || encodeURI;
  const path = options.url
    .replace('{api-version}', config.VERSION)
    .replace(/{(.*?)}/g, (substring: string, group: string) => {
      if (options.path?.hasOwnProperty(group)) {
        return encoder(String(options.path[group]));
      }
      return substring;
    });

  const url = `${config.BASE}${path}`;
  return options.query ? `${url}${getQueryString(options.query as Record<string, unknown>)}` : url;
};

/**
 * Prepara os dados de formulário para envio
 */
export const getFormData = (options: ApiRequestOptions): FormData | undefined => {
  if (!options.formData) return undefined;
  
  const formData = new FormData();
  const process = (key: string, value: unknown): void => {
    if (isString(value) || isBlob(value)) {
      formData.append(key, value);
    } else {
      formData.append(key, JSON.stringify(value));
    }
  };

  Object.entries(options.formData)
    .filter(([, value]) => isDefined(value))
    .forEach(([key, value]) => {
      if (Array.isArray(value)) value.forEach(v => process(key, v));
      else process(key, value);
    });
    
  return formData;
};

/**
 * Tipo para funções de resolução assíncrona
 */
type Resolver<T> = (options: ApiRequestOptions) => Promise<T>;

/**
 * Resolve um valor ou função assíncrona
 */
export const resolve = async <T>(
  options: ApiRequestOptions,
  resolver?: T | Resolver<T>
): Promise<T | undefined> => {
  if (typeof resolver === 'function') {
    return (resolver as Resolver<T>)(options);
  }
  return resolver;
};

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 4. HTTP REQUEST BUILDERS
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
/**
 * Monta os headers da requisição, incluindo autenticação
 */
export const getHeaders = (
  config: OpenAPIConfig,
  options: ApiRequestOptions
): Observable<HttpHeaders> => {
  return forkJoin({
    token:             resolve(options, config.TOKEN),
    username:          resolve(options, config.USERNAME),
    password:          resolve(options, config.PASSWORD),
    additionalHeaders: resolve(options, config.HEADERS),
  }).pipe(
    map(({ token, username, password, additionalHeaders }) => {
      const headers = Object.entries({
        Accept: 'application/json',
        ...additionalHeaders,
        ...options.headers,
      })
        .filter(([, value]) => isDefined(value))
        .reduce<Record<string, string>>(
          (acc, [key, value]) => ({ ...acc, [key]: String(value) }),
          {}
        );

      // Adiciona header de autenticação Bearer Token
      if (isStringWithValue(token)) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      // Adiciona header de autenticação Basic Auth
      if (isStringWithValue(username) && isStringWithValue(password)) {
        headers['Authorization'] = `Basic ${base64(`${username}:${password}`)}`;
      }
      
      // Define o Content-Type apropriado
      if (options.body !== undefined) {
        if (options.mediaType) {
          headers['Content-Type'] = options.mediaType;
        } else if (isBlob(options.body)) {
          headers['Content-Type'] = options.body.type || 'application/octet-stream';
        } else if (isString(options.body)) {
          headers['Content-Type'] = 'text/plain';
        } else if (!isFormData(options.body)) {
          headers['Content-Type'] = 'application/json';
        }
      }
      return new HttpHeaders(headers);
    })
  );
};

/**
 * Prepara o corpo da requisição
 */
export const getRequestBody = (options: ApiRequestOptions): unknown => {
  if (!isDefined(options.body)) return undefined;
  if (options.mediaType?.includes('/json')) {
    return JSON.stringify(options.body);
  }
  if (isString(options.body) || isBlob(options.body) || isFormData(options.body)) {
    return options.body;
  }
  return JSON.stringify(options.body);
};

/**
 * Envia a requisição HTTP
 */
export const sendRequest = <T>(
  config: OpenAPIConfig,
  options: ApiRequestOptions,
  http: HttpClient,
  url: string,
  body: unknown,
  formData: FormData | undefined,
  headers: HttpHeaders
): Observable<HttpResponse<T>> => {
  return http.request<T>(options.method, url, {
    headers,
    body: body ?? formData,
    withCredentials: config.WITH_CREDENTIALS,
    observe: 'response',
  });
};

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 5. RESPONSE HANDLERS
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
/**
 * Extrai um header específico da resposta
 */
export const getResponseHeader = <T>(
  response: HttpResponse<T>,
  responseHeader?: string
): string | undefined => {
  if (!responseHeader) return undefined;
  const value = response.headers.get(responseHeader);
  return isString(value) ? value : undefined;
};

/**
 * Extrai o corpo da resposta
 */
export const getResponseBody = <T>(response: HttpResponse<T>): T | undefined =>
  response.status !== 204 && response.body !== null ? response.body : undefined;

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 6. ERROR HANDLING
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
/**
 * Converte uma resposta HTTP bem-sucedida para o formato padrão ApiResult
 */
const toApiResult = <T>(response: HttpResponse<T>, url: string): ApiResult => {
  const responseBody = getResponseBody(response);
  const responseHeader = getResponseHeader(response, undefined);
  return {
    url,
    ok:         response.ok,
    status:     response.status,
    statusText: response.statusText,
    body:       responseHeader ?? responseBody,
  };
};

/**
 * Converte um erro HTTP para o formato padrão ApiResult
 */
const toApiResultFromError = (error: HttpErrorResponse, url: string): ApiResult => {
  return {
    url,
    ok:         error.ok,
    status:     error.status,
    statusText: error.statusText,
    body:       error.error ?? error.statusText,
  };
};

/**
 * Trata códigos de erro HTTP conhecidos
 */
export const catchErrorCodes = (options: ApiRequestOptions, result: ApiResult): void => {
  const errors: Record<number, string> = {
    400: 'Requisição Inválida',
    401: 'Não Autorizado',
    403: 'Acesso Negado',
    404: 'Não Encontrado',
    500: 'Erro Interno do Servidor',
    502: 'Gateway Ruim',
    503: 'Serviço Indisponível'
  };

  const error = errors[result.status];
  if (error) throw new ApiError(options, result, error);

  if (!result.ok) {
    const errorStatus     = result.status     ?? 'desconhecido';
    const errorStatusText = result.statusText ?? 'desconhecido';
    const errorBody = (() => {
      try { return JSON.stringify(result.body, null, 2); }
      catch { return undefined; }
    })();
    
    throw new ApiError(
      options,
      result,
      `Erro Genérico: status: ${errorStatus}; status text: ${errorStatusText}; body: ${errorBody}`
    );
  }
};

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 7. PIPELINE PRINCIPAL
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
/**
 * Pipeline principal de requisições HTTP
 * Responsável por orquestrar todas as etapas do ciclo de vida da requisição
 */
export const request = <T>(
  config: OpenAPIConfig,
  http: HttpClient,
  options: ApiRequestOptions
): Observable<T> => {
  const url = getUrl(config, options);
  const formData = getFormData(options);
  const body = getRequestBody(options);

  return getHeaders(config, options).pipe(
    switchMap(headers => 
      sendRequest<T>(config, options, http, url, body, formData, headers).pipe(
        map(response => toApiResult(response, url)),
        catchError((error: HttpErrorResponse) => {
          if (!error.status) return throwError(() => error);
          return of(toApiResultFromError(error, url));
        })
      )
    ),
    map((result: ApiResult) => {
      catchErrorCodes(options, result);
      return result.body as T;
    })
  );
};
