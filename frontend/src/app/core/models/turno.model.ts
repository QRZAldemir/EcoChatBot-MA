/**
 * EcoChatBot - Sistema de Atendimento
 * 
 * Arquivo: turno.model.ts
 * Descricao: Define as interfaces e tipos relacionados a turnos de trabalho.
 * Este arquivo contem as estruturas de dados para gerenciamento de horarios
 * e turnos de atendentes no sistema.
 * 
 * Autor: Aldemir Querioz
 * Data: 2026-10-05
 * Versao: 2.0.0
 */

import { Usuario } from './usuario.model';

/**
 * TurnoDia - Interface que representa um horario de turno em um dia
 * 
 * DESCRICAO:
 * Representa um intervalo de tempo em um dia do turno.
 * 
 * DESCRICAO DOS CAMPOS:
 * - ini: Hora de inicio no formato HH:MM (ex: "08:00")
 * - fim: Hora de termino no formato HH:MM (ex: "17:00")
 * 
 * FORMATO DE HORA:
 * - 24 horas (00:00 a 23:59)
 * - String no formato HH:MM
 * - O inicio deve ser anterior ao fim
 */
export interface TurnoDia {
    ini: string;
    fim: string;
}

/**
 * DiaSemana - Tipos de dias da semana
 * - dom: Domingo
 * - seg: Segunda-feira
 * - ter: Terca-feira
 * - qua: Quarta-feira
 * - qui: Quinta-feira
 * - sex: Sexta-feira
 * - sab: Sabado
 */
export type DiaSemana = 'dom' | 'seg' | 'ter' | 'qua' | 'qui' | 'sex' | 'sab';

/**
 * TurnoDias - Interface que agrupa turnos por dia da semana
 * 
 * DESCRICAO:
 * Contem os turnos para cada dia da semana.
 * Cada dia pode ter varios intervalos de turno.
 * 
 * DESCRICAO DOS CAMPOS:
 * - dom: Turnos para Domingo
 * - seg: Turnos para Segunda-feira
 * - ter: Turnos para Terca-feira
 * - qua: Turnos para Quarta-feira
 * - qui: Turnos para Quinta-feira
 * - sex: Turnos para Sexta-feira
 * - sab: Turnos para Sabado
 */
export interface TurnoDias {
    dom: TurnoDia[];
    seg: TurnoDia[];
    ter: TurnoDia[];
    qua: TurnoDia[];
    qui: TurnoDia[];
    sex: TurnoDia[];
    sab: TurnoDia[];
}

/**
 * Turno - Interface principal que representa um turno de trabalho
 * 
 * RELACIONAMENTOS:
 * - Usuario: Atraves de usuario.turno (N:1) - Varios usuarios podem pertencer a um turno
 * 
 * DESCRICAO:
 * Representa um turno de trabalho com horarios definidos para cada dia da semana.
 * 
 * DESCRICAO DOS CAMPOS:
 * - id: Identificador unico do turno (PK)
 * - desc: Descricao do turno
 * - dias: Objeto TurnoDias com horarios para cada dia
 * - acao: Acao a ser executada no inicio do turno (ex: "iniciar_atendimento")
 * - msgAndamento: Mensagem para quando o turno esta em andamento
 * - msgEncerramento: Mensagem para quando o turno esta sendo encerrado
 * - status: Status do turno ('ativo' | 'inativo')
 * 
 * ACIOES POSSIVEIS:
 * - iniciar_atendimento: Inicia atendimentos automaticos
 * - pausar_atendimento: Pausa novos atendimentos
 * - encerra_atendimento: Encerra atendimentos em andamento
 * 
 * USO NO PROJETO:
 * - Controle de horarios de atendentes
 * - Automatizacao de inicio/fim de jornada
 * - Mensagens automaticas baseadas em turno
 */
export interface Turno {
    id: number;
    desc: string;
    dias: TurnoDias;
    acao: string;
    msgAndamento: string;
    msgEncerramento: string;
    status: 'ativo' | 'inativo';
}

/**
 * DIAS_SEMANA - Array com os dias da semana e seus labels
 * Usado para populacao de selects e exibicao.
 */
export const DIAS_SEMANA: Array<{ key: DiaSemana; label: string }> = [
    { key: 'dom', label: 'Dom' },
    { key: 'seg', label: 'Seg' },
    { key: 'ter', label: 'Ter' },
    { key: 'qua', label: 'Qua' },
    { key: 'qui', label: 'Qui' },
    { key: 'sex', label: 'Sex' },
    { key: 'sab', label: 'Sáb' }
];

/**
 * MODELOS RELACIONADOS:
 * 
 * 1. Usuario (usuario.model.ts)
 *    - id: number (PK)
 *    - turno?: string (referencia ao Turno)
 *    - ... outros campos
 * 
 * REGRAS DE NEGOCIO:
 * - Turno -> Usuario: 1:N (Um turno pode ser atribuido a varios usuarios)
 * - Turnos inativos (status: 'inativo') nao sao considerados para distribuicao de atendimentos
 * - Um usuario so pode pertencer a UM turno por vez
 * - Os horarios sao usados para determinar disponibilidade de atendentes
 * - A acao e executada automaticamente no inicio do turno
 */
