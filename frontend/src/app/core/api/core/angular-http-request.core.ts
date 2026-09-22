/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/** Serviços de autenticação e sessão de usuário.
* Tratadores de erro globais.
* Interceptadores e clientes HTTP centralizados.*/

import { Inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import type { Observable } from 'rxjs';

import type { ApiRequestOptions } from './api-request-options.core';
import { BaseHttpRequest } from './base-http-request.core';
import type { OpenAPIConfig } from './open-api.core';
import { OpenAPI } from './open-api.core';
import { request as __request } from './request';

@Injectable()
export class AngularHttpRequest extends BaseHttpRequest {

    constructor(
        @Inject(OpenAPI)
        config: OpenAPIConfig,
        http: HttpClient,
    ) {
        super(config, http);
    }

    /**
     * Request method
     * @param options The request options from the service
     * @returns Observable<T>
     * @throws ApiError
     */
    public override request<T>(options: ApiRequestOptions): Observable<T> {
        return __request(this.config, this.http, options);
    }
}
