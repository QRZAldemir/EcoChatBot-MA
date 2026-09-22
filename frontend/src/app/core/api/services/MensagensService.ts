/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import { Injectable } from '@angular/core';
import type { Observable } from 'rxjs';
import type { EnviarMensagemRequest } from '../models/envia-mensagem-request.model';
import type { EnviarTemplateRequest } from '../models/envia-template-request.models';
import type { MenuEnviarRequest } from '../models/menu-envia-request.models';
import type { VerificarMensagemRequest } from '../models/verifica-mensagem-request.models';
import type { ZigResponse } from '../models/ZigResponse';
import { BaseHttpRequest } from '../core/base-http-request.core';
@Injectable({
    providedIn: 'root',
})
export class MensagensService {
    constructor(public readonly httpRequest: BaseHttpRequest) {}
    /**
     * Enviar Mensagem
     * Envia uma ou mais mensagens (texto e/ou arquivo) para um número via Evolution API.
     * Contrato compatível com ZigChat POST /mensagem/enviar.
     * @param requestBody
     * @returns ZigResponse Successful Response
     * @throws ApiError
     */
    public enviarMensagemApiMensagemEnviarPost(
        requestBody: EnviarMensagemRequest,
    ): Observable<ZigResponse> {
        return this.httpRequest.request({
            method: 'POST',
            url: '/api/mensagem/enviar',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Enviar Template
     * Envia um template WABA para um contato via Evolution API.
     * Contrato compatível com ZigChat POST /mensagem/template.
     * @param requestBody
     * @returns ZigResponse Successful Response
     * @throws ApiError
     */
    public enviarTemplateApiMensagemTemplatePost(
        requestBody: EnviarTemplateRequest,
    ): Observable<ZigResponse> {
        return this.httpRequest.request({
            method: 'POST',
            url: '/api/mensagem/template',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Menu Enviar
     * Envia um menu interativo (lista) para um cliente via Evolution API.
     * Contrato compatível com ZigChat POST /mensagem/menuEnviar.
     * @param requestBody
     * @returns ZigResponse Successful Response
     * @throws ApiError
     */
    public menuEnviarApiMensagemMenuEnviarPost(
        requestBody: MenuEnviarRequest,
    ): Observable<ZigResponse> {
        return this.httpRequest.request({
            method: 'POST',
            url: '/api/mensagem/menuEnviar',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Verificar Mensagem
     * Verifica se uma mensagem foi realmente enviada para o número informado.
     * Contrato compatível com ZigChat POST /mensagem/verificar.
     * @param requestBody
     * @returns ZigResponse Successful Response
     * @throws ApiError
     */
    public verificarMensagemApiMensagemVerificarPost(
        requestBody: VerificarMensagemRequest,
    ): Observable<ZigResponse> {
        return this.httpRequest.request({
            method: 'POST',
            url: '/api/mensagem/verificar',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
