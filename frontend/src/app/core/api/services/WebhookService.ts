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
export class WebhookService {
    constructor(public readonly httpRequest: BaseHttpRequest) {}
    /**
     * Evolution Webhook
     * Ponto de entrada para todos os eventos da Evolution API.
     *
     * A Evolution API exige resposta HTTP 200 em até ~5 s.
     * Todo o processamento pesado (DB + chamadas à Evolution) acontece
     * em background, garantindo retorno imediato.
     *
     * Segurança: se WEBHOOK_SECRET estiver configurado no .env, valida o
     * header 'apikey' ou 'authorization' enviado pela Evolution API.
     * @param instance
     * @returns any Successful Response
     * @throws ApiError
     */
    public evolutionWebhookApiWebhookInstancePost(
        instance: string,
    ): Observable<any> {
        return this.httpRequest.request({
            method: 'POST',
            url: '/api/webhook/{instance}',
            path: {
                'instance': instance,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
