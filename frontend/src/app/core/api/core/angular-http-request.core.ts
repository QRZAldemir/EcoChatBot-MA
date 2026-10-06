/**
 * @fileoverview AngularHttpRequest - Cliente HTTP centralizado para requisições à API
 * 
 * @author Sistema Gerado
 * @version 1.0.0
 * @since 2026-08-07
 * 
 * @description
 * Este serviço implementa um cliente HTTP centralizado para a aplicação Angular,
 * seguindo o padrão OpenAPI. Ele estende a classe BaseHttpRequest para fornecer
 * uma camada de abstração sobre o HttpClient do Angular, adicionando:
 * - Tratamento global de erros
 * - Interceptadores de requisição/resposta
 * - Configuração centralizada da API
 * - Suporte a tipagem genérica
 * 
 * @usage
 * Injetar AngularHttpRequest em serviços e componentes que precisam realizar
 * requisições HTTP à API backend.
 * 
 * @example
 * ```typescript
 * constructor(private http: AngularHttpRequest) {}
 * 
 * getData(): Observable<MyData> {
 *   return this.http.request({
 *     method: 'GET',
 *     url: '/api/data'
 *   });
 * }
 * ```
 */

/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import { Inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import type { Observable } from 'rxjs';

import type { ApiRequestOptions } from './api-request-options.core';
import { BaseHttpRequest } from './base-http-request.core';
import type { OpenAPIConfig } from './open-api.core';
import { OpenAPI } from './open-api.core';
import { request as __request } from './request.core';


/**
 * Serviço HTTP centralizado para comunicação com a API backend
 * 
 * @description
 * Esta classe implementa um cliente HTTP que:
 * 1. Herda de BaseHttpRequest para funcionalidades básicas
 * 2. Utiliza HttpClient do Angular para requisições HTTP
 * 3. Integra com a configuração OpenAPI
 * 4. Fornece tipagem genérica para respostas
 * 5. Centraliza o tratamento de erros e interceptadores
 * 
 * @template T - Tipo genérico para a resposta da requisição
 */
@Injectable({
  providedIn: 'root'
})
export class AngularHttpRequest extends BaseHttpRequest {
  /**
   * Injeta dependências necessárias
   * 
   * @param config Configuração OpenAPI injetada
   * @param HttpClient Instância do HttpClient do Angular
   */
  constructor(
    @Inject(OpenAPI)
    config: OpenAPIConfig,
    http: HttpClient,
  ) {
    super(config, http);
  }

  /**
   * Executa uma requisição HTTP à API
   * 
   * @param options Configurações da requisição (método, URL, headers, etc.)
   * @returns Observable com a resposta tipada
   * @throws ApiError Em caso de erro na requisição
   * 
   * @template T Tipo da resposta esperada
   */
  public override request<T>(options: ApiRequestOptions): Observable<T> {
    return __request(this.config, this.http, options);
  }
}
