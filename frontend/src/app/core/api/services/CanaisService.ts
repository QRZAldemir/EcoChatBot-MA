/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import { Injectable } from '@angular/core';
import type { Observable } from 'rxjs';
import type { CanalCreate } from '../models/canal-create.models';
import type { CanalResponse } from '../models/canal-response.models';
import type { CanalUpdate } from '../models/canal-update.models';
import { BaseHttpRequest } from '../core/base-http-request.core';
@Injectable({
    providedIn: 'root',
})
export class CanaisService {
    constructor(public readonly httpRequest: BaseHttpRequest) {}
    /**
     * Listar Canais
     * Lista todos os canais cadastrados no sistema.
     *
     * Retorna:
     * - List[CanalResponse]: Uma lista de todos os canais.
     * @returns CanalResponse Successful Response
     * @throws ApiError
     */
    public listarCanaisApiCanaisGet(): Observable<Array<CanalResponse>> {
        return this.httpRequest.request({
            method: 'GET',
            url: '/api/canais/',
        });
    }
    /**
     * Criar Canal
     * Cria um novo canal no sistema.
     *
     * Parâmetros:
     * - canal (CanalCreate): Dados do canal a ser criado.
     *
     * Retorna:
     * - CanalResponse: O canal recém-criado.
     *
     * Lança:
     * - HTTPException: Se já existir um canal com o mesmo nome (status 400).
     * @param requestBody
     * @returns CanalResponse Successful Response
     * @throws ApiError
     */
    public criarCanalApiCanaisPost(
        requestBody: CanalCreate,
    ): Observable<CanalResponse> {
        return this.httpRequest.request({
            method: 'POST',
            url: '/api/canais/',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Buscar Canal
     * Busca um canal específico pelo seu ID.
     *
     * Parâmetros:
     * - canal_id (int): O ID do canal a ser buscado.
     *
     * Retorna:
     * - CanalResponse: O canal encontrado.
     *
     * Lança:
     * - HTTPException: Se o canal não for encontrado (status 404).
     * @param canalId
     * @returns CanalResponse Successful Response
     * @throws ApiError
     */
    public buscarCanalApiCanaisCanalIdGet(
        canalId: number,
    ): Observable<CanalResponse> {
        return this.httpRequest.request({
            method: 'GET',
            url: '/api/canais/{canal_id}',
            path: {
                'canal_id': canalId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Atualizar Canal
     * Atualiza um canal existente no sistema.
     *
     * Parâmetros:
     * - canal_id (int): O ID do canal a ser atualizado.
     * - canal (CanalUpdate): Dados atualizados do canal.
     *
     * Retorna:
     * - CanalResponse: O canal atualizado.
     *
     * Lança:
     * - HTTPException: Se o canal não for encontrado (status 404) ou
     * se já existir um canal com o mesmo nome (status 400).
     * @param canalId
     * @param requestBody
     * @returns CanalResponse Successful Response
     * @throws ApiError
     */
    public atualizarCanalApiCanaisCanalIdPut(
        canalId: number,
        requestBody: CanalUpdate,
    ): Observable<CanalResponse> {
        return this.httpRequest.request({
            method: 'PUT',
            url: '/api/canais/{canal_id}',
            path: {
                'canal_id': canalId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Deletar Canal
     * Deleta um canal do sistema.
     *
     * Parâmetros:
     * - canal_id (int): O ID do canal a ser deletado.
     *
     * Retorna:
     * - None: Não há conteúdo para retornar após a exclusão (status 204).
     *
     * Lança:
     * - HTTPException: Se o canal não for encontrado (status 404).
     * @param canalId
     * @returns void
     * @throws ApiError
     */
    public deletarCanalApiCanaisCanalIdDelete(
        canalId: number,
    ): Observable<void> {
        return this.httpRequest.request({
            method: 'DELETE',
            url: '/api/canais/{canal_id}',
            path: {
                'canal_id': canalId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
