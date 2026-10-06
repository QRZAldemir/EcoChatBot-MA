/**
 * EcoChatBot - Sistema de Atendimento
 * 
 * Arquivo: arquivo.model.ts
 * Descricao: Define a interface para gerenciamento de arquivos anexados no sistema.
 * Este arquivo contem a estrutura de dados para armazenamento e gerenciamento de 
 * arquivos associados aos atendimentos, incluindo metadados e relacionamentos.
 * 
 * Autor: Aldemir Querioz
 * Data: 2026-10-05
 * Versao: 2.0.0
 */

import { Atendimento } from './atendimento.model';

/**
 * Arquivo - Interface que representa um arquivo anexado no sistema
 * 
 * RELACIONAMENTOS:
 * - Atendimento: Atraves de atendimentoId (N:1) - Um arquivo pertence a UM atendimento
 * 
 * DESCRICAO:
 * Interface responsavel por representar arquivos anexados aos atendimentos.
 * Contem metadados essenciais para identificacao, manipulacao e exibicao dos arquivos.
 * 
 * DESCRICAO DOS CAMPOS:
 * - id: Identificador unico do arquivo (PK)
 * - nomeOriginal: Nome original do arquivo quando foi enviado
 * - tipoMime: Tipo MIME do arquivo (ex: 'image/png', 'application/pdf') - opcional
 * - tamanhoBytes: Tamanho do arquivo em bytes - opcional
 * - descricao: Descricao opcional do arquivo
 * - atendimentoId: FK para o atendimento ao qual o arquivo esta associado (Atendimento['id']) - opcional
 * - criadoEm: Data/hora de criacao do registro do arquivo (formato ISO)
 * 
 * USO NO PROJETO:
 * - Armazenamento de arquivos enviados por clientes ou atendentes
 * - Anexos de comprovantes, documentos, imagens em atendimentos
 * - Gerenciamento de midias trocadas durante o atendimento
 * 
 * NOTA TECNICA:
 * - Import de Atendimento: Cria RELACIONAMENTO DE DEPENDENCIA com atendimento.model.ts
 * - O tipo Atendimento['id'] garante consistencia com o tipo do ID no modelo Atendimento
 * - Se o tipo de ID em Atendimento mudar, este arquivo sera automaticamente atualizado
 */
export interface Arquivo {
  id: number;
  nomeOriginal: string;
  tipoMime?: string;
  tamanhoBytes?: number;
  descricao?: string;
  atendimentoId?: Atendimento['id'];
  criadoEm: string;
}

/**
 * MODELOS RELACIONADOS (para referencia):
 * 
 * 1. Atendimento (atendimento.model.ts)
 *    - id: number (PK)
 *    - protocolo: string
 *    - status: StatusAtendimento
 *    - departamentoId?: number
 *    - canalId?: number
 *    - usuarioId?: number
 *    - criadoEm?: string
 *    - atualizadoEm?: string
 * 
 * REGRAS DE NEGOCIO:
 * - Um Arquivo pertence a exatamenta um Atendimento (N:1)
 * - Um Atendimento pode ter varios Arquivos associados (1:N)
 * - Arquivos sem atendimentoId sao considerados orfaos e podem ser limbos periodicamente
 * - O campo criadoEm e obrigatorio e deve ser preenchido no momento do upload
 * - O campo nomeOriginal deve preservar a extensao do arquivo original
 */
