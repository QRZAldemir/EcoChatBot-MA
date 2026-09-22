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
export class MonitoramentoService {
    constructor(public readonly httpRequest: BaseHttpRequest) {}
    /**
     * Health Check
     * Endpoint de Health Check.
     * Utilizado por orquestradores de contêineres (Docker, Kubernetes) ou
     * ferramentas de monitoramento (UptimeRobot, Datadog) para verificar se
     * a aplicação está viva e apta a receber tráfego.
     * @returns string Successful Response
     * @throws ApiError
     */
    public healthCheckHealthGet(): Observable<Record<string, string>> {
        return this.httpRequest.request({
            method: 'GET',
            url: '/health',
        });
    }
}
