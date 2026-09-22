/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import { Injectable } from '@angular/core';
import type { Observable } from 'rxjs';
import type { CriarAlteraContextRequest } from '../models/criar-altera-context-request.models';
import type { DeletarContextRequest } from '../models/deletar-context-request.models';
import type { EncerrarAtendimentoRequest } from '../models/encerrar-atendimento-request.models';
import type { TransferirAtendimentoRequest } from '../models/transferir-atendimento-request.models';
import type { ZigResponse } from '../models/ZigResponse';
import { BaseHttpRequest } from '../core/base-http-request.core';
@Injectable({
    providedIn: 'root',
})
export class AtendimentoService {
    constructor(public readonly httpRequest: BaseHttpRequest) {}
    /**
     * Listar Atendimentos
     * Lista atendimentos de forma paginada com múltiplos filtros.
     * Contrato compatível com ZigChat GET /atendimento/listar (+ filtro
     * opcional "status", que é uma extensão própria deste projeto).
     * @param id Código do atendimento
     * @param canal 1=WhatsApp, 2=Interno
     * @param ativo S=Ativo, N=Inativo
     * @param dataCriacaoInicio
     * @param dataCriacaoFim
     * @param tipo 1=automático, 2=manual
     * @param departamentoId
     * @param atendenteUsuarioId
     * @param clienteId
     * @param protocolo
     * @param conexaoId
     * @param status aberto, fila, em_atendimento ou finalizado
     * @param limit
     * @param page
     * @param order
     * @returns ZigResponse Successful Response
     * @throws ApiError
     */
    public listarAtendimentosApiAtendimentoListarGet(
        id?: (number | null),
        canal?: (number | null),
        ativo?: (string | null),
        dataCriacaoInicio?: (string | null),
        dataCriacaoFim?: (string | null),
        tipo?: (number | null),
        departamentoId?: (number | null),
        atendenteUsuarioId?: (number | null),
        clienteId?: (number | null),
        protocolo?: (string | null),
        conexaoId?: (number | null),
        status?: (string | null),
        limit: number = 10,
        page: number = 1,
        order: string = 'desc',
    ): Observable<ZigResponse> {
        return this.httpRequest.request({
            method: 'GET',
            url: '/api/atendimento/listar',
            query: {
                'id': id,
                'canal': canal,
                'ativo': ativo,
                'data_criacao_inicio': dataCriacaoInicio,
                'data_criacao_fim': dataCriacaoFim,
                'tipo': tipo,
                'departamento_id': departamentoId,
                'atendente_usuario_id': atendenteUsuarioId,
                'cliente_id': clienteId,
                'protocolo': protocolo,
                'conexao_id': conexaoId,
                'status': status,
                'limit': limit,
                'page': page,
                'order': order,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Indicadores Atendimentos
     * Indicadores de atendimento em tempo real, direto do banco — substitui o
     * fluxo manual de extrair relatório da ZigChat, exportar em Excel e
     * importar no dashboard. Endpoint próprio deste projeto (não é contrato
     * ZigChat); pensado para ser consultado por polling do painel/dashboard.
     * @param dataCriacaoInicio
     * @param dataCriacaoFim
     * @returns ZigResponse Successful Response
     * @throws ApiError
     */
    public indicadoresAtendimentosApiAtendimentoIndicadoresGet(
        dataCriacaoInicio?: (string | null),
        dataCriacaoFim?: (string | null),
    ): Observable<ZigResponse> {
        return this.httpRequest.request({
            method: 'GET',
            url: '/api/atendimento/indicadores',
            query: {
                'data_criacao_inicio': dataCriacaoInicio,
                'data_criacao_fim': dataCriacaoFim,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Consultar Context
     * Consulta um contexto do atendimento pela context_key.
     * Contrato compatível com ZigChat GET /atendimento/context/{atendimentoID}/{context_key}.
     * @param atendimentoId
     * @param contextKey
     * @returns ZigResponse Successful Response
     * @throws ApiError
     */
    public consultarContextApiAtendimentoContextAtendimentoIdContextKeyGet(
        atendimentoId: number,
        contextKey: string,
    ): Observable<ZigResponse> {
        return this.httpRequest.request({
            method: 'GET',
            url: '/api/atendimento/context/{atendimentoID}/{context_key}',
            path: {
                'atendimentoID': atendimentoId,
                'context_key': contextKey,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Transferir Atendimento
     * Transfere o atendimento para um departamento, atendente e/ou canal, e
     * avisa o paciente por WhatsApp sobre a mudança.
     * Contrato compatível com ZigChat POST /atendimento/transferir.
     * @param requestBody
     * @returns ZigResponse Successful Response
     * @throws ApiError
     */
    public transferirAtendimentoApiAtendimentoTransferirPost(
        requestBody: TransferirAtendimentoRequest,
    ): Observable<ZigResponse> {
        return this.httpRequest.request({
            method: 'POST',
            url: '/api/atendimento/transferir',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Encerrar Atendimento
     * Encerra um atendimento, alterando seu status para 'finalizado'.
     * Se uma mensagem for informada, envia o texto via Evolution API (WhatsApp) antes de encerrar.
     * É uma função 'async' porque precisa aguardar (await) a resposta da API externa.
     * Contrato compatível com ZigChat POST /atendimento/encerrar.
     * @param requestBody
     * @returns ZigResponse Successful Response
     * @throws ApiError
     */
    public encerrarAtendimentoApiAtendimentoEncerrarPost(
        requestBody: EncerrarAtendimentoRequest,
    ): Observable<ZigResponse> {
        return this.httpRequest.request({
            method: 'POST',
            url: '/api/atendimento/encerrar',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Deletar Context
     * Deleta um contexto do atendimento pela context_key.
     * Contrato compatível com ZigChat POST /atendimento/deletarContext.
     * @param requestBody
     * @returns ZigResponse Successful Response
     * @throws ApiError
     */
    public deletarContextApiAtendimentoDeletarContextPost(
        requestBody: DeletarContextRequest,
    ): Observable<ZigResponse> {
        return this.httpRequest.request({
            method: 'POST',
            url: '/api/atendimento/deletarContext',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Criar Altera Context
     * Adiciona ou atualiza um contexto no atendimento (operação de Upsert).
     * Se a context_key já existir para aquele atendimento, sobrescreve o value.
     * Contrato compatível com ZigChat POST /atendimento/criarAlteraContext.
     * @param requestBody
     * @returns ZigResponse Successful Response
     * @throws ApiError
     */
    public criarAlteraContextApiAtendimentoCriarAlteraContextPost(
        requestBody: CriarAlteraContextRequest,
    ): Observable<ZigResponse> {
        return this.httpRequest.request({
            method: 'POST',
            url: '/api/atendimento/criarAlteraContext',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
