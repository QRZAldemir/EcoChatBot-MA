/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import { Injectable } from '@angular/core';
import type { Observable } from 'rxjs';
import type { LoginRequest } from '../models/login-request.model';
import type { LoginResponse } from '../models/login-response.model';
import { BaseHttpRequest } from '../core/base-http-request.core';
@Injectable({
    providedIn: 'root',
})
export class AutenticacaoService {
    constructor(public readonly httpRequest: BaseHttpRequest) {}
    /**
     * Login
     * Autentica um usuário do painel administrativo por e-mail/senha e
     * retorna um JWT para as próximas requisições.
     * @param requestBody
     * @returns LoginResponse Successful Response
     * @throws ApiError
     */
    public loginApiAuthLoginPost(
        requestBody: LoginRequest,
    ): Observable<LoginResponse> {
        return this.httpRequest.request({
            method: 'POST',
            url: '/api/auth/login',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
