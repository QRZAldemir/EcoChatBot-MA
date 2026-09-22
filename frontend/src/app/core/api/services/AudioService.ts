/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import { Injectable } from '@angular/core';
import type { Observable } from 'rxjs';
import type { GerarAudioRequest } from '../models/gera-audio-resquest.models';
import type { GerarAudioResponse } from '../models/gera-audio-response.models';
import { BaseHttpRequest } from '../core/base-http-request.core';
@Injectable({
    providedIn: 'root',
})
export class AudioService {
    constructor(public readonly httpRequest: BaseHttpRequest) {}
    /**
     * Gerar Audio
     * Converte um texto (ex: conteúdo de um Memorando) em áudio MP3 via
     * síntese de voz, para acessibilidade de usuários com deficiência
     * visual ou motora.
     * @param requestBody
     * @returns GerarAudioResponse Successful Response
     * @throws ApiError
     */
    public gerarAudioApiAudioGerarPost(
        requestBody: GerarAudioRequest,
    ): Observable<GerarAudioResponse> {
        return this.httpRequest.request({
            method: 'POST',
            url: '/api/audio/gerar',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Servir Audio
     * Serve um arquivo de áudio previamente gerado por POST /gerar.
     * @param nomeArquivo
     * @returns any Successful Response
     * @throws ApiError
     */
    public servirAudioApiAudioAudiosNomeArquivoGet(
        nomeArquivo: string,
    ): Observable<any> {
        return this.httpRequest.request({
            method: 'GET',
            url: '/api/audio/audios/{nome_arquivo}',
            path: {
                'nome_arquivo': nomeArquivo,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
