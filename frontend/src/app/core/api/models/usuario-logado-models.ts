/*Os arquivos que ficam dentro dessa pasta servem para **definir a estrutura, o formato e a tipagem dos dados** que circulam na aplicação
/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type UsuarioLogado = {
    id:               number;
    nome:             string;
    email:            string;
    nivel?:           (string | null);
    departamento_id?: (number | null);
    empresa_id:       (number |null);
    canal_id?:        (number | null);

};

