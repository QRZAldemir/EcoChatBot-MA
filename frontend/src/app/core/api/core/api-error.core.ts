/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/** Serviços de autenticação e sessão de usuário.
* Tratadores de erro globais.
* Interceptadores e clientes HTTP centralizados.*/
/** Serviços de autenticação e sessão de usuário.
* Tratadores de erro globais.
* Interceptadores e clientes HTTP centralizados.*/


import type { ApiRequestOptions } from './api-request-options.core';
import type { ApiResult } from './api-result.core';

export class ApiError extends Error {
    public readonly url: string;
    public readonly status: number;
    public readonly statusText: string;
    public readonly body: any;
    public readonly request: ApiRequestOptions;

    constructor(request: ApiRequestOptions, response: ApiResult, message: string) {
        super(message);

        this.name = 'ApiError';
        this.url = response.url;
        this.status = response.status;
        this.statusText = response.statusText;
        this.body = response.body;
        this.request = request;
    }
}
