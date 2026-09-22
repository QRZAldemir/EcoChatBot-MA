/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { MensagemItem } from './mensagem-item.models';
export type EnviarMensagemRequest = {
    mensagens: Array<MensagemItem>;
    telefone: string;
    lid?: (string | null);
    cliente_id?: (number | null);
    conexao: string;
    nome?: (string | null);
    transferir?: boolean;
    interna?: boolean;
    verifica_numero?: boolean;
    finalizarAtendimento?: boolean;
};

