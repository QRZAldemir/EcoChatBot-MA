/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { MensagemItem } from './mensagem-item.models';
export type MenuEnviarRequest = {
    mensagens: Array<MensagemItem>;
    telefone: string;
    lid?: (string | null);
    cliente_id?: (number | null);
    conexao: string;
    nome?: (string | null);
    menu_id: string;
};

