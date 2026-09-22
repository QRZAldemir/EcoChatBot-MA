/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import { NgModule} from '@angular/core';
import { HttpClientModule } from '@angular/common/http';
import { AngularHttpRequest } from './core/angular-HttpRequest.core';
import { BaseHttpRequest } from './core/base-http-request.core';
import type { OpenAPIConfig } from './core/open-api.core';
import { OpenAPI } from './core/open-api.core';
import { AtendimentoService } from './services/AtendimentoService';
import { AudioService } from './services/AudioService';
import { AutenticacaoService } from './services/AutenticacaoService';
import { CanaisService } from './services/CanaisService';
import { DepartamentosService } from './services/DepartamentosService';
import { InteligenciaArtificialService } from './services/InteligenciaArtificialService';
import { MensagensService } from './services/MensagensService';
import { MenusService } from './services/MenusService';
import { ModelosDeMensagemService } from './services/ModelosDeMensagemService';
import { MonitoramentoService } from './services/MonitoramentoService';
import { RootService } from './services/RootService';
import { UsuariosService } from './services/usuarioservice';
import { WebhookService } from './services/WebhookService';
@NgModule({
    imports: [HttpClientModule],
    providers: [
        {
            provide: OpenAPI,
            useValue: {
                BASE: OpenAPI?.BASE ?? '',
                VERSION: OpenAPI?.VERSION ?? '1.0.0',
                WITH_CREDENTIALS: OpenAPI?.WITH_CREDENTIALS ?? false,
                CREDENTIALS: OpenAPI?.CREDENTIALS ?? 'include',
                TOKEN: OpenAPI?.TOKEN,
                USERNAME: OpenAPI?.USERNAME,
                PASSWORD: OpenAPI?.PASSWORD,
                HEADERS: OpenAPI?.HEADERS,
                ENCODE_PATH: OpenAPI?.ENCODE_PATH,
            } as OpenAPIConfig,
        },
        {
            provide: BaseHttpRequest,
            useClass: AngularHttpRequest,
        },
        AtendimentoService,
        AudioService,
        AutenticacaoService,
        CanaisService,
        DepartamentosService,
        InteligenciaArtificialService,
        MensagensService,
        MenusService,
        ModelosDeMensagemService,
        MonitoramentoService,
        RootService,
        UsuariosService,
        WebhookService,
    ]
})
export class EcoChatApiClient {}

