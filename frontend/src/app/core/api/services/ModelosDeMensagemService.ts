/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import { Injectable } from '@angular/core';
import type { Observable } from 'rxjs';
import type { ModeloMensagemCreate } from '../models/mensagem-create.models';
import type { ModeloMensagemResponse } from '../models/mensagem-response.models';
import type { ModeloMensagemUpdate } from '../models/mensagem-update.models';
import { BaseHttpRequest } from '../core/base-http-request.core';
@Injectable({
    providedIn: 'root',
})
export class ModelosDeMensagemService {
    constructor(public readonly httpRequest: BaseHttpRequest) {}
    /**
     * Listar Modelos
     * @param departamentoId
     * @param apenasAtivos
     * @returns ModeloMensagemResponse Successful Response
     * @throws ApiError
     */
    public listarModelosApiModelosMensagemGet(
        departamentoId?: (number | null),
        apenasAtivos: boolean = false,
    ): Observable<Array<ModeloMensagemResponse>> {
        return this.httpRequest.request({
            method: 'GET',
            url: '/api/modelos-mensagem/',
            query: {
                'departamento_id': departamentoId,
                'apenas_ativos': apenasAtivos,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Criar Modelo
     * @param requestBody
     * @returns ModeloMensagemResponse Successful Response
     * @throws ApiError
     */
    public criarModeloApiModelosMensagemPost(
        requestBody: ModeloMensagemCreate,
    ): Observable<ModeloMensagemResponse> {
        return this.httpRequest.request({
            method: 'POST',
            url: '/api/modelos-mensagem/',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Buscar Modelo
     * @param modeloId
     * @returns ModeloMensagemResponse Successful Response
     * @throws ApiError
     */
    public buscarModeloApiModelosMensagemModeloIdGet(
        modeloId: number,
    ): Observable<ModeloMensagemResponse> {
        return this.httpRequest.request({
            method: 'GET',
            url: '/api/modelos-mensagem/{modelo_id}',
            path: {
                'modelo_id': modeloId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Atualizar Modelo
     * @param modeloId
     * @param requestBody
     * @returns ModeloMensagemResponse Successful Response
     * @throws ApiError
     */
    public atualizarModeloApiModelosMensagemModeloIdPut(
        modeloId: number,
        requestBody: ModeloMensagemUpdate,
    ): Observable<ModeloMensagemResponse> {
        return this.httpRequest.request({
            method: 'PUT',
            url: '/api/modelos-mensagem/{modelo_id}',
            path: {
                'modelo_id': modeloId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Deletar Modelo
     * @param modeloId
     * @returns void
     * @throws ApiError
     */
    public deletarModeloApiModelosMensagemModeloIdDelete(
        modeloId: number,
    ): Observable<void> {
        return this.httpRequest.request({
            method: 'DELETE',
            url: '/api/modelos-mensagem/{modelo_id}',
            path: {
                'modelo_id': modeloId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
