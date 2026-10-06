/**
 * EcoChatBot - Sistema de Atendimento
 * 
 * Arquivo: modelo-mensagem.model.ts
 * Descricao: Define a interface para modelos de mensagens pre-definidas.
 * Este arquivo contem a estrutura de dados para gerenciamento de modelos
 * de mensagens que podem ser usadas como templates em atendimentos.
 * 
 * Autor: Aldemir Querioz
 * Data: 2026-10-05
 * Versao: 2.0.0
 */

import { Departamento } from './departamento.model';

/**
 * ModeloMensagem - Interface que representa um modelo de mensagem
 * 
 * RELACIONAMENTOS:
 * - Departamento: Atraves de departamentoId (N:1) - Um modelo pertence a UM departamento
 * 
 * DESCRICAO:
 * Representa um modelo de mensagem pre-definida que pode ser usado
 * como template em atendimentos ou campanhas.
 * 
 * DESCRICAO DOS CAMPOS:
 * - id: Identificador unico do modelo (PK)
 * - descricao: Descricao do modelo para identificacao
 * - corpo: Corpo da mensagem (conteudo)
 * - arquivo: Caminho para arquivo anexo - opcional
 * - departamentoId: FK para o departamento associado - opcional
 * - departamentoNome: Nome do departamento associado - opcional
 * - ativo: Indica se o modelo esta ativo
 * - criadoEm: Data/hora de criacao (formato ISO) - opcional
 * 
 * USO NO PROJETO:
 * - Templates de mensagens rapidas
 * - Respostas padrao para atendimentos
 * - Mensagens pre-definidas para campanhas
 * 
 * FUNCIONALIDADES:
 * - Variaveis de substituicao podem ser usadas no corpo (ex: {{nome}}, {{protocolo}})
 * - O campo 'arquivo' pode conter um template HTML ou texto plano
 */
export interface ModeloMensagem {
  id: number;
  descricao: string;
  corpo: string;
  arquivo?: string;
  departamentoId?: Departamento['id'];
  departamentoNome?: string;
  ativo: boolean;
  criadoEm?: string;
}

/**
 * MODELOS RELACIONADOS:
 * 
 * 1. Departamento (departamento.model.ts)
 *    - id: number (PK)
 *    - nome: string
 *    - descricao?: string
 *    - ... outros campos
 * 
 * REGRAS DE NEGOCIO:
 * - ModeloMensagem -> Departamento: N:1 (Varios modelos podem pertencer a um departamento)
 * - Modelos inativos (ativo: false) nao aparecem nas listas de selecao
 * - O corpo da mensagem pode conter variaveis de substituicao
 * - O arquivo (se existir) e um caminho para um template externo
 */
