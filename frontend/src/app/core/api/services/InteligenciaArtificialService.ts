/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import { Injectable } from '@angular/core';
import type { Observable } from 'rxjs';
import type { ConversaRequest } from '../models/conversa-request.model';
import type { OpcaoRequest } from '../models/opcao-request.models';
import type { RespostaIA } from '../models/resposta-ia.models';
import { BaseHttpRequest } from '../core/base-http-request.core';
@Injectable({
    providedIn: 'root',
})
export class InteligenciaArtificialService {
    constructor(public readonly httpRequest: BaseHttpRequest) {}
    /**
     * Conversar Ia
     * @param requestBody
     * @returns RespostaIA Successful Response
     * @throws ApiError
     */
    public conversarIaApiIaConversarPost(
        requestBody: ConversaRequest,
    ): Observable<RespostaIA> {
        return this.httpRequest.request({
            method: 'POST',
            url: '/api/ia/conversar',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Responder Opcao
     * @param requestBody
     * @returns RespostaIA Successful Response
     * @throws ApiError
     */
    public responderOpcaoApiIaOpcaoPost(
        requestBody: OpcaoRequest,
    ): Observable<RespostaIA> {
        return this.httpRequest.request({
            method: 'POST',
            url: '/api/ia/opcao',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
