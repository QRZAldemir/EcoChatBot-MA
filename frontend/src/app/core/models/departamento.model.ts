/**
 * EcoChatBot - Sistema de Atendimento
 * 
 * Arquivo: departamento.model.ts
 * Descricao: Define a interface para departamentos do sistema.
 * Este arquivo contem a estrutura de dados para gerenciamento de departamentos,
 * que sao usados para organizar atendimentos, usuarios e canais.
 * 
 * Autor: Aldemir Querioz
 * Data: 2026-10-05
 * Versao: 2.0.0
 */

/**
 * Departamento - Interface que representa um departamento
 * 
 * RELACIONAMENTOS:
 * - Usuario: Atraves de usuario.departamentoId (1:N) - Um departamento pode ter varios usuarios
 * - Canal: Atraves de canal.departamentoId (1:N) - Um departamento pode ter varios canais
 * - Atendimento: Atraves de atendimento.departamentoId (1:N) - Um departamento pode ter varios atendimentos
 * - Campanha: Atraves de campanha.conexaoId -> Conexao -> Canal (N:N) - Departamentos usam canais para campanhas
 * - ModeloMensagem: Atraves de modeloMensagem.departamentoId (1:N) - Um departamento pode ter varios modelos de mensagem
 * 
 * DESCRICAO:
 * Representa um departamento no sistema.
 * Departamentos sao usados para organizar e categorizar atendimentos,
 * usuarios e canais de comunicacao.
 * 
 * DESCRICAO DOS CAMPOS:
 * - id: Identificador unico do departamento (PK)
 * - nome: Nome do departamento
 * - descricao: Descricao do departamento - opcional
 * - desc: Descricao alternativa (campo legado) - opcional
 * - ativo: Indica se o departamento esta ativo - opcional
 * - status: Status do departamento ('ativo' | 'inativo') - opcional
 * - criado_em: Data/hora de criacao (formato ISO, snake_case) - opcional
 * 
 * USO NO PROJETO:
 * - Organizacao de atendimentos por area
 * - Agrupamento de usuarios por departamento
 * - Associacao de canais a departamentos
 * - Filtro de atendimentos e relatorios
 */
export interface Departamento {
  id: number;
  nome: string;
  descricao?: string;
  desc?: string;
  ativo?: boolean;
  status?: 'ativo' | 'inativo';
  criado_em?: string;
}

/**
 * MODELOS RELACIONADOS:
 * 
 * 1. Usuario (usuario.model.ts)
 *    - id: number (PK)
 *    - departamentoId?: number (FK)
 *    - ... outros campos
 * 
 * 2. Canal (canal.model.ts)
 *    - id: number (PK)
 *    - departamentoId?: number (FK)
 *    - departamentoNome?: string
 *    - ... outros campos
 * 
 * 3. Atendimento (atendimento.model.ts)
 *    - id: number (PK)
 *    - departamentoId?: number (FK)
 *    - ... outros campos
 * 
 * REGRAS DE NEGOCIO:
 * - Departamento -> Usuario: 1:N (Um departamento pode ter varios usuarios)
 * - Departamento -> Canal: 1:N (Um departamento pode ter varios canais)
 * - Departamento -> Atendimento: 1:N (Um departamento pode ter varios atendimentos)
 * - Departamento -> ModeloMensagem: 1:N (Um departamento pode ter varios modelos de mensagem)
 * - Departamentos inativos (ativo: false ou status: 'inativo') nao aparecem em listas padrao
 */