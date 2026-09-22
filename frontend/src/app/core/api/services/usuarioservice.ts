/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import { Injectable } from '@angular/core';
import type { Observable } from 'rxjs';
import type { UsuarioCreate } from '../models/usuario-creator.models';
import type { UsuarioListItem } from '../models/usuario-listaitens-models';
import type { UsuarioResponse } from '../models/usuario_response.model';
import type { UsuarioUpdate } from '../models/usuario_update.models';
import { BaseHttpRequest } from '../core/base-http-request.core';
@Injectable({
    providedIn: 'root',
})
export class UsuariosService {
    constructor(public readonly httpRequest: BaseHttpRequest) {}
    /**
     * Listar Usuarios
     * @param nome
     * @param departamentoId
     * @param canalId
     * @param nivel
     * @param status
     * @returns UsuarioListItem Successful Response
     * @throws ApiError
     */
    public listarUsuariosApiUsuariosGet(
        nome?: (string | null),
        departamentoId?: (number | null),
        canalId?: (number | null),
        nivel?: (string | null),
        status?: (string | null),
    ): Observable<Array<UsuarioListItem>> {
        return this.httpRequest.request({
            method: 'GET',
            url: '/api/usuarios/',
            query: {
                'nome': nome,
                'departamentoId': departamentoId,
                'canalId': canalId,
                'nivel': nivel,
                'status': status,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Criar Usuario
     * @param requestBody
     * @returns UsuarioResponse Successful Response
     * @throws ApiError
     */
    public criarUsuarioApiUsuariosPost(
        requestBody: UsuarioCreate,
    ): Observable<UsuarioResponse> {
        return this.httpRequest.request({
            method: 'POST',
            url: '/api/usuarios/',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Buscar Usuario
     * @param usuarioId
     * @returns UsuarioResponse Successful Response
     * @throws ApiError
     */
    public buscarUsuarioApiUsuariosUsuarioIdGet(
        usuarioId: number,
    ): Observable<UsuarioResponse> {
        return this.httpRequest.request({
            method: 'GET',
            url: '/api/usuarios/{usuario_id}',
            path: {
                'usuario_id': usuarioId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Atualizar Usuario
     * @param usuarioId
     * @param requestBody
     * @returns UsuarioResponse Successful Response
     * @throws ApiError
     */
    public atualizarUsuarioApiUsuariosUsuarioIdPut(
        usuarioId: number,
        requestBody: UsuarioUpdate,
    ): Observable<UsuarioResponse> {
        return this.httpRequest.request({
            method: 'PUT',
            url: '/api/usuarios/{usuario_id}',
            path: {
                'usuario_id': usuarioId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Deletar Usuario
     * @param usuarioId
     * @returns void
     * @throws ApiError
     */
    public deletarUsuarioApiUsuariosUsuarioIdDelete(
        usuarioId: number,
    ): Observable<void> {
        return this.httpRequest.request({
            method: 'DELETE',
            url: '/api/usuarios/{usuario_id}',
            path: {
                'usuario_id': usuarioId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
