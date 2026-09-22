/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import { Injectable } from '@angular/core';
import type { Observable } from 'rxjs';
import type { DepartamentoCreate } from '../models/departamento-create.models';
import type { DepartamentoResponse } from '../models/departamento-response.models';
import type { DepartamentoUpdate } from '../models/departamento-update.models';
import { BaseHttpRequest } from '../core/base-http-request.core';
@Injectable({
    providedIn: 'root',
})
export class DepartamentosService {
    constructor(public readonly httpRequest: BaseHttpRequest) {}
    /**
     * Listar Departamentos
     * Lista todos os departamentos cadastrados no sistema.
     *
     * Retorna:
     * - List[DepartamentoResponse]: Uma lista de todos os departamentos.
     * @returns DepartamentoResponse Successful Response
     * @throws ApiError
     */
    public listarDepartamentosApiDepartamentosGet(): Observable<Array<DepartamentoResponse>> {
        return this.httpRequest.request({
            method: 'GET',
            url: '/api/departamentos/',
        });
    }
    /**
     * Criar Departamento
     * Cria um novo departamento no sistema.
     *
     * Parâmetros:
     * - departamento (DepartamentoCreate): Dados do departamento a ser criado.
     *
     * Retorna:
     * - DepartamentoResponse: O departamento recém-criado.
     * @param requestBody
     * @returns DepartamentoResponse Successful Response
     * @throws ApiError
     */
    public criarDepartamentoApiDepartamentosPost(
        requestBody: DepartamentoCreate,
    ): Observable<DepartamentoResponse> {
        return this.httpRequest.request({
            method: 'POST',
            url: '/api/departamentos/',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Buscar Departamento
     * Busca um departamento específico pelo seu ID.
     *
     * Parâmetros:
     * - departamento_id (int): O ID do departamento a ser buscado.
     *
     * Retorna:
     * - DepartamentoResponse: O departamento encontrado.
     *
     * Lança:
     * - HTTPException: Se o departamento não for encontrado (status 404).
     * @param departamentoId
     * @returns DepartamentoResponse Successful Response
     * @throws ApiError
     */
    public buscarDepartamentoApiDepartamentosDepartamentoIdGet(
        departamentoId: number,
    ): Observable<DepartamentoResponse> {
        return this.httpRequest.request({
            method: 'GET',
            url: '/api/departamentos/{departamento_id}',
            path: {
                'departamento_id': departamentoId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Atualizar Departamento
     * Atualiza um departamento existente no sistema.
     *
     * Parâmetros:
     * - departamento_id (int): O ID do departamento a ser atualizado.
     * - departamento (DepartamentoUpdate): Dados atualizados do departamento.
     *
     * Retorna:
     * - DepartamentoResponse: O departamento atualizado.
     *
     * Lança:
     * - HTTPException: Se o departamento não for encontrado (status 404).
     * @param departamentoId
     * @param requestBody
     * @returns DepartamentoResponse Successful Response
     * @throws ApiError
     */
    public atualizarDepartamentoApiDepartamentosDepartamentoIdPut(
        departamentoId: number,
        requestBody: DepartamentoUpdate,
    ): Observable<DepartamentoResponse> {
        return this.httpRequest.request({
            method: 'PUT',
            url: '/api/departamentos/{departamento_id}',
            path: {
                'departamento_id': departamentoId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Deletar Departamento
     * Deleta um departamento do sistema.
     *
     * Parâmetros:
     * - departamento_id (int): O ID do departamento a ser deletado.
     *
     * Retorna:
     * - None: Não há conteúdo para retornar após a exclusão (status 204).
     *
     * Lança:
     * - HTTPException: Se o departamento não for encontrado (status 404).
     * @param departamentoId
     * @returns void
     * @throws ApiError
     */
    public deletarDepartamentoApiDepartamentosDepartamentoIdDelete(
        departamentoId: number,
    ): Observable<void> {
        return this.httpRequest.request({
            method: 'DELETE',
            url: '/api/departamentos/{departamento_id}',
            path: {
                'departamento_id': departamentoId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
