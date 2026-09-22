/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import { Injectable } from '@angular/core';
import type { Observable } from 'rxjs';
import type { MenuCreate } from '../models/menu-create.models';
import type { MenuOpcaoCreate } from '../models/menu-opcao-create.models';
import type { MenuOpcaoResponse } from '../models/menu-opcao-response.models';
import type { MenuOpcaoUpdate } from '../models/menu-opcao-update.models';
import type { MenuResponse } from '../models/menu-response.models';
import type { MenuUpdate } from '../models/menu-update.models';
import { BaseHttpRequest } from '../core/base-http-request.core';
@Injectable({
    providedIn: 'root',
})
export class MenusService {
    constructor(public readonly httpRequest: BaseHttpRequest) {}
    /**
     * Listar Menus
     * @param canalId
     * @param apenasAtivos
     * @returns MenuResponse Successful Response
     * @throws ApiError
     */
    public listarMenusApiMenusGet(
        canalId?: (number | null),
        apenasAtivos: boolean = false,
    ): Observable<Array<MenuResponse>> {
        return this.httpRequest.request({
            method: 'GET',
            url: '/api/menus/',
            query: {
                'canal_id': canalId,
                'apenas_ativos': apenasAtivos,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Criar Menu
     * @param requestBody
     * @returns MenuResponse Successful Response
     * @throws ApiError
     */
    public criarMenuApiMenusPost(
        requestBody: MenuCreate,
    ): Observable<MenuResponse> {
        return this.httpRequest.request({
            method: 'POST',
            url: '/api/menus/',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Buscar Menu
     * @param menuId
     * @returns MenuResponse Successful Response
     * @throws ApiError
     */
    public buscarMenuApiMenusMenuIdGet(
        menuId: number,
    ): Observable<MenuResponse> {
        return this.httpRequest.request({
            method: 'GET',
            url: '/api/menus/{menu_id}',
            path: {
                'menu_id': menuId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Atualizar Menu
     * @param menuId
     * @param requestBody
     * @returns MenuResponse Successful Response
     * @throws ApiError
     */
    public atualizarMenuApiMenusMenuIdPut(
        menuId: number,
        requestBody: MenuUpdate,
    ): Observable<MenuResponse> {
        return this.httpRequest.request({
            method: 'PUT',
            url: '/api/menus/{menu_id}',
            path: {
                'menu_id': menuId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Deletar Menu
     * @param menuId
     * @returns void
     * @throws ApiError
     */
    public deletarMenuApiMenusMenuIdDelete(
        menuId: number,
    ): Observable<void> {
        return this.httpRequest.request({
            method: 'DELETE',
            url: '/api/menus/{menu_id}',
            path: {
                'menu_id': menuId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Adicionar Opcao
     * @param menuId
     * @param requestBody
     * @returns MenuOpcaoResponse Successful Response
     * @throws ApiError
     */
    public adicionarOpcaoApiMenusMenuIdOpcoesPost(
        menuId: number,
        requestBody: MenuOpcaoCreate,
    ): Observable<MenuOpcaoResponse> {
        return this.httpRequest.request({
            method: 'POST',
            url: '/api/menus/{menu_id}/opcoes',
            path: {
                'menu_id': menuId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Atualizar Opcao
     * @param opcaoId
     * @param requestBody
     * @returns MenuOpcaoResponse Successful Response
     * @throws ApiError
     */
    public atualizarOpcaoApiMenusOpcoesOpcaoIdPut(
        opcaoId: number,
        requestBody: MenuOpcaoUpdate,
    ): Observable<MenuOpcaoResponse> {
        return this.httpRequest.request({
            method: 'PUT',
            url: '/api/menus/opcoes/{opcao_id}',
            path: {
                'opcao_id': opcaoId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Deletar Opcao
     * @param opcaoId
     * @returns void
     * @throws ApiError
     */
    public deletarOpcaoApiMenusOpcoesOpcaoIdDelete(
        opcaoId: number,
    ): Observable<void> {
        return this.httpRequest.request({
            method: 'DELETE',
            url: '/api/menus/opcoes/{opcao_id}',
            path: {
                'opcao_id': opcaoId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
