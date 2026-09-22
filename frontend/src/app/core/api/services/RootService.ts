/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import { Injectable } from '@angular/core';
import type { Observable } from 'rxjs';
import { BaseHttpRequest } from '../core/base-http-request.core';
@Injectable({
    providedIn: 'root',
})
export class RootService {
    constructor(public readonly httpRequest: BaseHttpRequest) {}
    /**
     * Read Root
     * Endpoint raiz. Serve como uma mensagem de boas-vindas e confirmação
     * de que a API está respondendo a requisições HTTP.
     * @returns string Successful Response
     * @throws ApiError
     */
    public readRootGet(): Observable<Record<string, string>> {
        return this.httpRequest.request({
            method: 'GET',
            url: '/',
        });
    }
}
