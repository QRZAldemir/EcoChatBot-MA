/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { HttpClient } from '@angular/common/http';
import type { Observable } from 'rxjs';

import type { ApiRequestOptions } from './api-request-options.core';
import type { OpenAPIConfig } from './open-api.core';

export abstract class BaseHttpRequest {

    constructor(
        public readonly config: OpenAPIConfig,
        public readonly http: HttpClient,
    ) {}

    public abstract request<T>(options: ApiRequestOptions): Observable<T>;
}
