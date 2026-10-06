/**
 * EcoChatBot - Sistema de Atendimento
 * 
 * Arquivo: nivel-usuario.model.ts
 * Descricao: Define os tipos e interfaces relacionados a niveis de usuario e permissoes.
 * Este arquivo contem as estruturas de dados para gerenciamento de niveis de
 * acesso e controle de permissoes no sistema.
 * 
 * Autor: Aldemir Querioz
 * Data: 2026-10-05
 * Versao: 2.0.0
 */

/**
 * NivelAcesso - Tipos de niveis de acesso do sistema
 * 
 * HIERARQUIA DE PERMISSOES:
 * administrador > gerente > supervisor > atendente
 * 
 * DESCRICAO DOS NIVEIS:
 * - atendente: Acesso basico, pode atender chamados
 * - supervisor: Pode supervisionar atendentes e ver relatorios
 * - gerente: Pode gerenciar departments, canais e usuarios
 * - administrador: Acesso completo ao sistema
 */
export type NivelAcesso = 'atendente' | 'supervisor' | 'gerente' | 'administrador';

/**
 * Permissao - Interface que representa permissoes em um modulo
 * 
 * RELACIONAMENTOS:
 * - NivelUsuario: Atraves de permissoes[] (1:N) - Um nivel pode ter varias permissoes
 * 
 * DESCRICAO:
 * Representa as permissoes de um nivel de usuario para um modulo especifico.
 * 
 * DESCRICAO DOS CAMPOS:
 * - modulo: Nome do modulo (ex: 'atendimento', 'campanha', 'relatorios')
 * - leitura: Permissao de leitura (ver dados)
 * - escrita: Permissao de escrita (criar, editar)
 * - exclusao: Permissao de exclusao (remover dados)
 * 
 * MODULOS COMUNS:
 * - atendimento: Gerenciamento de atendimentos
 * - campanha: Gerenciamento de campanhas
 * - usuario: Gerenciamento de usuarios
 * - relatorios: Acesso a relatorios
 * - configuracoes: Acesso as configuracoes do sistema
 */
export interface Permissao {
  modulo: string;
  leitura: boolean;
  escrita: boolean;
  exclusao: boolean;
}

/**
 * NivelUsuario - Interface que representa um nivel de usuario com permissoes
 * 
 * RELACIONAMENTOS:
 * - Usuario: Atraves de usuario.nivel (1:N) - Varios usuarios podem ter o mesmo nivel
 * - Auth: Atraves de UsuarioLogado.nivel (1:N) - Usuarios logados tem um nivel
 * 
 * DESCRICAO:
 * Representa um nivel de usuario no sistema com suas permissoes detalhadas.
 * Cada nivel define o que o usuario pode ou nao fazer.
 * 
 * DESCRICAO DOS CAMPOS:
 * - id: Identificador unico do nivel (PK)
 * - nome: Nome do nivel (ex: 'Atendente', 'Supervisor')
 * - codigo: Codigo do nivel (NivelAcesso)
 * - descricao: Descricao do nivel
 * - permissoes: Array de Permissao para cada modulo
 * - ativo: Indica se o nivel esta ativo
 * 
 * PERMISSOES PADRAO POR NIVEL:
 * - atendente: leitura, escrita em atendimento
 * - supervisor: leitura em todos, escrita em atendimento
 * - gerente: leitura e escrita em todos, exclusao em atendimento
 * - administrador: leitura, escrita, exclusao em todos os modulos
 */
export interface NivelUsuario {
  id: number;
  nome: string;
  codigo: NivelAcesso;
  descricao: string;
  permissoes: Permissao[];
  ativo: boolean;
}

/**
 * MODELOS RELACIONADOS:
 * 
 * 1. Usuario (usuario.model.ts)
 *    - id: number (PK)
 *    - nivel?: NivelAcesso
 *    - ... outros campos
 * 
 * 2. UsuarioLogado (auth.model.ts)
 *    - id: number (PK)
 *    - nivel?: NivelAcesso
 *    - ... outros campos
 * 
 * REGRAS DE NEGOCIO:
 * - NivelUsuario -> Usuario: 1:N (Um nivel pode ser atribuido a varios usuarios)
 * - NivelUsuario -> Permissao: 1:N (Um nivel pode ter varias permissoes)
 * - Niveis inativos (ativo: false) nao podem ser atribuidos a novos usuarios
 * - O nivel 'administrador' nao pode ser excluido
 * - As permissoes sao cumulativas (niveis superiores herdam permissoes de inferiores)
 */
