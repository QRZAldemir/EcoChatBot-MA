/**
 * EcoChatBot - Sistema de Atendimento
 * 
 * Arquivo: dashboard.model.ts
 * Descricao: Define as interfaces para o painel de controle (dashboard).
 * Este arquivo contem as estruturas de dados para exibicao de metricas,
 * estatisticas, filtros e relatorios no painel administrativo.
 * 
 * NOTA: As interfaces aqui sao ESPECIFICAS para o dashboard e podem se sobrepor
 * a interfaces similares em outros arquivos, mas com campos adaptados para
 * visualizacao e relatorios. Elas usam NOMES em vez de IDs para facilitar display.
 * 
 * Autor: Aldemir Querioz
 * Data: 2026-10-05
 * Versao: 2.0.0
 */

import { Departamento } from './departamento.model';
import { Usuario } from './usuario.model';
import { StatusAtendimento } from './atendimento.model';
import { Canal } from './canal.model';

/**
 * Atendimento - Interface de atendimento OTIMIZADA PARA DASHBOARD
 * 
 * NOTA: Esta interface e diferente de Atendimento em atendimento.model.ts
 * Ela contem campos otimizados para visualizacao no dashboard (usando NOMES em vez de IDs).
 * 
 * RELACIONAMENTOS:
 * - Departamento: Atraves de departamento (string) - Nome do departamento
 * - Usuario: Atraves de atendente (string) - Nome do atendente
 * - Canal: Atraves de canal (string) - Nome do canal
 * 
 * DESCRICAO:
 * Representa um atendimento com campos adaptados para exibicao no dashboard.
 * Contem dados resumidos e formatados para relatorios e visualizacao.
 * 
 * DESCRICAO DOS CAMPOS:
 * - id: Identificador do atendimento - opcional
 * - protocolo: Protocolo do atendimento
 * - nome: Nome do cliente ou contato
 * - departamento: Nome do departamento (NAO e ID, e o nome para display)
 * - atendente: Nome do atendente (NAO e ID, e o nome para display)
 * - canal: Nome do canal (NAO e ID, e o nome para display) - opcional
 * - telefone: Telefone do contato - opcional
 * - dataCriacao: Data de criacao (Date ou string para flexibilidade)
 * - dataFinalizacao: Data de finalizacao - opcional (Date ou string)
 * - status: Status do atendimento ('aberto' | 'finalizado' | 'aguardando')
 * - tipo: Tipo do atendimento ('humano' | 'robo')
 * - observacao: Observacoes - opcional
 * - finalizadosSemAtendimento: Contador de finalizados sem atendimento - opcional
 * - aguardandoAtendimento: Contador de aguardando atendimento - opcional
 * - iniciadoPor: Nome de quem inicio o atendimento - opcional
 * 
 * DIFERENCA PARA atendimento.model.ts:
 * - Campos usam NOMES (strings) em vez de IDs para display
 * - Campos opcionais para flexibilidade do dashboard
 * - Campos de contagem (finalizadosSemAtendimento, aguardandoAtendimento)
 * - Campo 'canal' adiconado para identificacao do canal de origem
 * 
 * USO NO PROJETO:
 * - Listagem de atendimentos no dashboard
 * - Relatorios e estatisticas
 * - Visualizacao rapida de status e metricas
 */
export interface Atendimento {
  id?: number;
  protocolo: string;
  nome: string;
  departamento: string;  // Nome do departamento (NAO ID, para display)
  atendente: string;    // Nome do atendente (NAO ID, para display)
  canal?: string;       // Nome do canal (NAO ID, para display) - opcional
  telefone?: string;
  dataCriacao: Date | string;
  dataFinalizacao?: Date | string;
  status: 'aberto' | 'finalizado' | 'aguardando';
  tipo: 'humano' | 'robo';
  observacao?: string;
  finalizadosSemAtendimento?: string;
  aguardandoAtendimento?: string;
  iniciadoPor?: string;
}

/**
 * AtendimentoStats - Interface de estatisticas de atendimentos
 * 
 * DESCRICAO:
 * Contem metricas e estatisticas calculadas sobre atendimentos.
 * Usada para exibicao de KPIs no dashboard.
 * 
 * DESCRICAO DOS CAMPOS:
 * - total: Total de atendimentos
 * - humanos: Quantidade de atendimentos humanos
 * - robos: Quantidade de atendimentos por robo
 * - emAberto: Quantidade de atendimentos em aberto
 * - tma: Tempo Medio de Atendimento (em minutos)
 * - tme: Tempo Medio de Espera (em minutos)
 * 
 * CALCULOS:
 * - tma = (soma de todos os tempos de atendimento) / total
 * - tme = (soma de todos os tempos de espera) / total
 * 
 * USO NO PROJETO:
 * - Exibicao de KPIs no dashboard
 * - Monitoramento de performance
 * - Alertas de SLA
 */
export interface AtendimentoStats {
  total: number;
  humanos: number;
  robos: number;
  emAberto: number;
  tma: number;  // Tempo Medio de Atendimento (minutos)
  tme: number;  // Tempo Medio de Espera (minutos)
}

/**
 * Avaliacao - Interface de avaliacao de atendimento
 * 
 * RELACIONAMENTOS:
 * - Atendimento: Atraves de atendimentoId (N:1) - Uma avaliacao pertence a UM atendimento
 * - Departamento: Atraves de departamento (string) - Nome do departamento
 * 
 * DESCRICAO:
 * Representa uma avaliacao feita por um cliente apos um atendimento.
 * 
 * DESCRICAO DOS CAMPOS:
 * - id: Identificador unico da avaliacao (PK)
 * - atendimentoId: FK para o atendimento avaliado
 * - nota: Nota dada (1-5 ou 1-10, dependendo do sistema)
 * - departamento: Nome do departamento do atendimento
 * - data: Data da avaliacao
 * - comentario: Comentario do cliente - opcional
 * 
 * USO NO PROJETO:
 * - Exibicao de avaliacoes no dashboard
 * - Calculode nota media por atendente/departamento
 * - Feedback de clientes
 */
export interface Avaliacao {
  id: number;
  atendimentoId: number;
  nota: number;
  departamento: string;
  data: Date;
  comentario?: string;
}

/**
 * FilterOptions - Interface de opcoes de filtro para dashboard
 * 
 * DESCRICAO:
 * Contem as opcoes disponiveis para filtragem no dashboard.
 * Usa IDs e nomes para populacao de dropdowns.
 * 
 * DESCRICAO DOS CAMPOS:
 * - departamentos: Array de departamentos para filtro (id e nome)
 * - atendentes: Array de atendentes para filtro (id e nome)
 * - canais: Array de canais para filtro (id e nome) - NOVO
 * - status: Array de status para filtro (id e nome)
 * 
 * USO NO PROJETO:
 * - Populacao de dropdowns de filtro
 * - Opcoes de selecao no dashboard
 * - Filtros por departamento, atendente, canal ou status
 */
export interface FilterOptions {
  departamentos: { id: Departamento['id']; nome: Departamento['nome'] }[];
  atendentes: { id: Usuario['id']; nome: Usuario['nome'] }[];
  canais: { id: Canal['id']; nome: Canal['nome'] }[];  // NOVO: Filtro por canal
  status: { id: StatusAtendimento | string; nome: string }[];
}

/**
 * FilterValues - Interface de valores de filtro selecionados
 * 
 * DESCRICAO:
 * Contem os valores selecionados pelo usuario para filtragem.
 * 
 * DESCRICAO DOS CAMPOS:
 * - dataIni: Data inicial do filtro - opcional
 * - dataFim: Data final do filtro - opcional
 * - departamento: Nome ou ID do departamento - opcional
 * - atendente: Nome ou ID do atendente - opcional
 * - canal: Nome ou ID do canal - opcional (NOVO)
 * - status: Status selecionado - opcional
 * - search: Termo de busca - opcional
 * - notaMin: Nota minima para filtro - opcional
 * - notaMax: Nota maxima para filtro - opcional
 * 
 * USO NO PROJETO:
 * - Aplicacao de filtros no dashboard
 * - Pesquisa de dados historicos
 * - Geracao de relatorios personalizados
 * - Filtro por canal, departamento, atendente, etc.
 */
export interface FilterValues {
  dataIni?: Date;
  dataFim?: Date;
  departamento?: string;
  atendente?: string;
  canal?: string;  // NOVO: Filtro por canal
  status?: string;
  search?: string;
  notaMin?: number;
  notaMax?: number;
}

/**
 * MODELOS RELACIONADOS:
 * 
 * 1. Departamento (departamento.model.ts)
 *    - id: number (PK)
 *    - nome: string
 *    - ... outros campos
 * 
 * 2. Usuario (usuario.model.ts)
 *    - id: number (PK)
 *    - nome: string
 *    - ... outros campos
 * 
 * 3. Atendimento (atendimento.model.ts)
 *    - id: number (PK)
 *    - status: StatusAtendimento
 *    - ... outros campos
 * 
 * REGRAS DE NEGOCIO:
 * - Atendimento (dashboard) e uma versao otimizada para visualizacao
 * - FilterOptions usa dados reais de Departamento e Usuario
 * - FilterValues contem os parametros de filtragem selecionados
 * - Avaliacao -> Atendimento: N:1 (Varias avaliacoes para um atendimento)
 * - As estatisticas sao calculadas em tempo real ou cacheadas
 */