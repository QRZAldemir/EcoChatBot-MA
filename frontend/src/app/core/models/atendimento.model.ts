/**
 * EcoChatBot - Sistema de Atendimento
 * 
 * Arquivo: atendimento.model.ts
 * Descricao: Define as interfaces e tipos relacionados ao modulo de atendimento.
 * Este arquivo contem as estruturas de dados para gerenciamento de atendimentos,
 * incluindo status, filtros e os relacionamentos com outros modelos do sistema.
 * 
 * FLUXO DE ATENDIMENTO:
 * 1. Cliente entra em contato via Canal (WhatsApp, Telegram, etc.)
 * 2. Sistema identifica o Menu do Canal
 * 3. Cliente seleciona opcao no Menu
 * 4. Sistema identifica Departamento da opcao
 * 5. Sistema cria Atendimento com:
 *    - canalId: Canal de origem
 *    - departamentoId: Departamento da opcao selecionada
 *    - menuItemId: Opcao selecionada (opcional)
 *    - status: 'aberto'
 * 6. Atendente do Departamento atende o cliente
 * 
 * Autor: Aldemir Querioz
 * Data: 2026-10-05
 * Versao: 2.0.0
 */

import { Departamento } from './departamento.model';
import { Canal } from './canal.model';
import { Usuario } from './usuario.model';

/**
 * StatusAtendimento - Tipos de status possiveis para um atendimento
 * 
 * RELACIONAMENTOS:
 * - Nenhum (tipo primitivo)
 * 
 * DESCRICAO:
 * Define os estados possiveis de um atendimento no sistema:
 * - aberto: Atendimento criado, aguardando triagem ou atendente
 * - fila: Atendimento na fila de espera para ser atendido
 * - em_atendimento: Atendimento sendo processado por um atendente
 * - finalizado: Atendimento concluido
 */
export type StatusAtendimento = 'aberto' | 'fila' | 'em_atendimento' | 'finalizado';

/**
 * Atendimento - Interface principal que representa um atendimento no sistema
 * 
 * RELACIONAMENTOS:
 * - Departamento: Atraves de departamentoId (N:1) - Um atendimento pertence a UM departamento
 * - Canal: Atraves de canalId (N:1) - Um atendimento e realizado por UM canal de comunicacao
 * - Usuario: Atraves de usuarioId (N:1) - Um atendimento e associado a UM usuario (atendente)
 * - Contato: Atraves de telefone (N:1) - Um atendimento e associado a UM contato
 * - MenuItem: Atraves de menuItemId (N:1) - Um atendimento pode ser originado de uma opcao de menu
 * 
 * DESCRICAO:
 * Representa uma conversa em andamento entre um cliente e a empresa.
 * Contem todas as informacoes necessarias para rastreamento e gerenciamento.
 * 
 * DESCRICAO DOS CAMPOS:
 * - id: Identificador unico do atendimento (PK)
 * - protocolo: Codigo unico gerado para rastreamento do atendimento
 * - telefone: Telefone do contato (opcional, depende do canal)
 * - nomeContato: Nome do contato/cliente (opcional)
 * - status: Estado atual do atendimento (StatusAtendimento)
 * - departamentoId: FK para o departamento responsavel (OBRIGATORIO) - departamento da opcao do menu
 * - canalId: FK para o canal de origem (OBRIGATORIO) - canal pelo qual o cliente entrou em contato
 * - usuarioId: FK para o usuario atendente (opcional) - atendente responsavel
 * - menuItemId: FK para a opcao do menu selecionada (opcional)
 * - criadoEm: Data/hora de criacao do atendimento (formato ISO)
 * - atualizadoEm: Data/hora da ultima atualizacao (formato ISO)
 * 
 * NOTA:
 * - O campo 'telefone' e opcional porque pode ser obtido do Contato
 * - O campo 'nomeContato' e opcional porque pode ser obtido do Contato
 * - O campo 'departamentoId' e determinando pelo MenuItem selecionado
 * - O campo 'canalId' e determinado pelo Canal de origem do contato
 */
export interface Atendimento {
  id: number;
  protocolo: string;
  telefone?: string;
  nomeContato?: string;
  status: StatusAtendimento;
  departamentoId: Departamento['id'];  // Departamento responsavel (OBRIGATORIO)
  canalId: Canal['id'];  // Canal de origem (OBRIGATORIO)
  usuarioId?: Usuario['id'];  // Atendente responsavel (opcional)
  menuItemId?: number;  // Opcao do menu selecionada (opcional)
  criadoEm?: string;
  atualizadoEm?: string;
}

/**
 * FiltroAtendimento - Interface para filtragem de atendimentos na API
 * 
 * RELACIONAMENTOS:
 * - Departamento: Atraves de departamentoId - Filtra atendimentos por departamento
 * - Usuario: Atraves de atendenteUsuarioId - Filtra atendimentos por atendente
 * - Canal: Atraves de canalId - Filtra atendimentos por canal (opcional)
 * 
 * OBSERVACOES:
 * - canalId pode ser usado para filtrar por canal especifico
 * - departamentoId filtra por departamento responsavel
 * - atendenteUsuarioId filtra por usuario atendente
 * 
 * DESCRICAO DOS CAMPOS:
 * - departamentoId: Filtra por ID do departamento (Departamento['id'])
 * - atendenteUsuarioId: Filtra por ID do usuario atendente (Usuario['id'])
 * - canalId: Filtra por ID do canal (Canal['id']) - opcional
 * - status: Filtra por status do atendimento (StatusAtendimento)
 * - dataCriacaoInicio: Data inicial para filtragem por criacao (formato AAAA-MM-DD)
 * - dataCriacaoFim: Data final para filtragem por criacao (formato AAAA-MM-DD)
 * - limit: Limite de resultados por pagina
 * - page: Numero da pagina (base 1)
 */
export interface FiltroAtendimento {
  departamentoId?: Departamento['id'];
  atendenteUsuarioId?: Usuario['id'];
  canalId?: Canal['id'];
  status?: StatusAtendimento;
  dataCriacaoInicio?: string; // formato AAAA-MM-DD
  dataCriacaoFim?: string;    // formato AAAA-MM-DD
  limit?: number;
  page?: number;
}

/**
 * MODELOS RELACIONADOS (para referencia):
 * 
 * 1. Departamento (departamento.model.ts)
 *    - id: number
 *    - nome: string
 *    - descricao?: string
 *    
 * 2. Canal (canal.model.ts) 
 *    - id: number
 *    - nome: string
 *    - tipo: 'whatsapp' | 'telegram' | 'email' | 'chat'
 *    
 * 3. Usuario (usuario.model.ts)
 *    - id: number
 *    - nome: string
 *    - email: string
 *    - perfil: 'admin' | 'atendente' | 'cliente'
 * 
 * REGRAS DE NEGOCIO:
 * - Um Atendimento pertence a exatamenta um Departamento (N:1)
 * - Um Atendimento e realizado por exatamenta um Canal (N:1)
 * - Um Atendimento pode ser atribuido a um Usuario (N:1)
 * - Um Departamento pode ter varios Atendimentos (1:N)
 * - Um Canal pode ter varios Atendimentos (1:N)
 * - Um Usuario pode ter varios Atendimentos atribuidos (1:N)
 */
