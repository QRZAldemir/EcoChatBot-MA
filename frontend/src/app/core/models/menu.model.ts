/**
 * EcoChatBot - Sistema de Atendimento
 * 
 * Arquivo: menu.model.ts
 * Descricao: Define as interfaces para menus apresentados aos clientes.
 * Menu = Estrutura de opcoes apresentadas ao cliente em um canal.
 * 
 * FLUXO:
 * 1. Cliente entra em contato via um Canal
 * 2. Sistema exibe o Menu associado ao Canal
 * 3. Cliente seleciona uma opcao (MenuOpcao)
 * 4. Sistema direciona para o Departamento associado a opcao
 * 5. Departamento tem usuarios com niveis de acesso
 * 6. Atendente do departamento atende o cliente
 * 
 * Autor: Aldemir Querioz
 * Data: 2026-10-05
 * Versao: 2.0.0
 */

import { Canal } from './canal.model';
import { Departamento } from './departamento.model';
import { Usuario } from './usuario.model';

/**
 * CorOpcao - Cores disponiveis para opcoes de menu
 * - verde: Cor verde
 * - azul: Cor azul
 * - vermelho: Cor vermelha
 * - amarelo: Cor amarela
 * - roxo: Cor roxa
 * - cinza: Cor cinza
 */
export type CorOpcao = 'verde' | 'azul' | 'vermelho' | 'amarelo' | 'roxo' | 'cinza';

/**
 * CORES_OPCAO - Array com todas as cores disponiveis
 * Usado para populacao de selects e validacao.
 */
export const CORES_OPCAO: CorOpcao[] = ['verde', 'azul', 'vermelho', 'amarelo', 'roxo', 'cinza'];

/**
 * MenuOpcao - Interface que representa uma opcao em um menu
 * 
 * RELACIONAMENTOS:
 * - Menu: Atraves de menuId (N:1) - Uma opcao pertence a UM menu
 * - Departamento: Atraves de departamentoId (N:1) - Uma opcao aponta para UM departamento
 * - Roteiro: Atraves de roteiroId (N:1) - Uma opcao pode ter UM roteiro opcional
 * 
 * DESCRICAO:
 * Representa uma opcao dentro de um menu interativo apresentado ao cliente.
 * Cada opcao define para onde o cliente sera direcionado.
 * 
 * FLUXO DE SELECAO:
 * 1. Cliente ve a opcao no menu
 * 2. Cliente seleciona a opcao
 * 3. Sistema identifica o departamentoId da opcao
 * 4. Sistema direciona para usuarios do departamento
 * 5. Se roteiroId existir, carrega o roteiro, senao vai direto para atendente
 * 
 * DESCRICAO DOS CAMPOS:
 * - id: Identificador unico da opcao (PK) - opcional
 * - menuId: FK para o menu ao qual pertence - opcional
 * - titulo: Titulo da opcao (texto exibido ao cliente)
 * - descricao: Descricao da opcao - opcional
 * - rowId: Identificador da linha (usado para agrupar opcoes) - opcional
 * - ordem: Ordem de exibicao no menu (1, 2, 3...)
 * - cor: Cor da opcao (CorOpcao) - opcional
 * - departamentoId: FK para o departamento que atende (OBRIGATORIO) ⭐
 * - roteiroId: FK para o roteiro opcional - opcional
 * - atalho: Atalho para selecao rapida (ex: "1", "AG") - opcional
 * - transfereDireto: Se true, pula roteiro e vai direto para atendente - opcional
 * - ativo: Indica se a opcao esta ativa
 * 
 * USO NO PROJETO:
 * - Itens de menu interativo
 * - Direcionamento para departamentos
 * - Fluxos de atendimento
 */
export interface MenuOpcao {
  id?: number;
  menuId?: number;
  titulo: string;
  descricao?: string;
  rowId?: string;
  ordem: number;
  cor?: CorOpcao;
  // ⭐ CAMPOS NOVOS CONFORME LOGICA DO PROJETO:
  departamentoId: Departamento['id'];  // Departamento que atende (OBRIGATORIO)
  roteiroId?: number;  // Roteiro opcional
  atalho?: string;  // Atalho para selecao rapida
  transfereDireto?: boolean;  // Pula roteiro, vai direto para atendente
  ativo?: boolean;
}

/**
 * Menu - Interface principal que representa um menu
 * 
 * RELACIONAMENTOS:
 * - Canal: Atraves de canalId (N:1) - Um menu pertence a UM canal
 * - MenuOpcao: Contem array de opcoes (1:N) - Um menu tem varias opcoes
 * - Usuario: Atraves de usuarioVinculadoId (N:1) - Um menu pode ser vinculado a UM usuario opcional
 * 
 * DESCRICAO:
 * Representa um menu interativo apresentado ao cliente quando ele entra em contato.
 * Cada menu e associado a um canal e contem opcoes que direcionam para departamentos.
 * 
 * FLUXO COMPLETO:
 * 1. Cliente entra em contato via Canal (WhatsApp, Telegram, etc.)
 * 2. Sistema identifica o Canal do contato
 * 3. Sistema carrega o Menu associado ao Canal
 * 4. Sistema exibe as opcoes (MenuOpcao) para o cliente
 * 5. Cliente seleciona uma opcao
 * 6. Sistema direciona para o Departamento da opcao
 * 7. Sistema guarda o Atendimento com o departamentoId
 * 
 * DESCRICAO DOS CAMPOS:
 * - id: Identificador unico do menu (PK)
 * - canalId: FK para o canal associado (OBRIGATORIO)
 * - titulo: Titulo do menu
 * - descricao: Descricao do menu - opcional
 * - saudacao: Mensagem de saudacao inicial - opcional
 * - rodape: Mensagem de rodape - opcional
 * - tempoEsperaSeg: Tempo de espera em segundos (default: 300 = 5 min) - opcional
 * - tentativasMax: Maximo de tentativas - opcional
 * - fallbackDepartamentoId: Departamento padrao se opcao invalida - opcional
 * - usuarioVinculadoId: FK para usuario vinculado - opcional
 * - usuarioVinculadoNome: Nome do usuario vinculado - opcional
 * - ativo: Indica se o menu esta ativo
 * - criadoEm: Data/hora de criacao (formato ISO) - opcional
 * - opcoes: Array de MenuOpcao (opcoes do menu)
 * 
 * USO NO PROJETO:
 * - Menus interativos em canais de comunicacao
 * - Direcionamento de clientes para departamentos
 * - Automatizacao de fluxos de atendimento
 */
export interface Menu {
  id: number;
  canalId: Canal['id'];  // Canal ao qual pertence (OBRIGATORIO)
  titulo: string;
  descricao?: string;
  saudacao?: string;
  rodape?: string;
  tempoEsperaSeg?: number;  // Tempo de espera em segundos
  tentativasMax?: number;  // Maximo de tentativas
  fallbackDepartamentoId?: Departamento['id'];  // Departamento padrao
  usuarioVinculadoId?: Usuario['id'];
  usuarioVinculadoNome?: string;
  ativo: boolean;
  criadoEm?: string;
  opcoes: MenuOpcao[];
}

/**
 * MODELOS RELACIONADOS:
 * 
 * 1. Canal (canal.model.ts)
 *    - id: number (PK)
 *    - tipo: TipoCanal (whatsapp, telegram, discord, pabx_voip, etc.)
 *    - telefone?: string
 *    - ... outros campos
 * 
 * 2. Departamento (departamento.model.ts)
 *    - id: number (PK)
 *    - nome: string
 *    - descricao?: string
 *    - ... outros campos
 * 
 * 3. Usuario (usuario.model.ts)
 *    - id: number (PK)
 *    - departamentoId?: number
 *    - ... outros campos
 * 
 * REGRAS DE NEGOCIO:
 * - Menu -> Canal: N:1 (Varios menus podem pertencer a um canal)
 * - Menu -> MenuOpcao: 1:N (Um menu pode ter varias opcoes)
 * - MenuOpcao -> Departamento: N:1 (Cada opcao aponta para UM departamento)
 * - MenuOpcao -> Roteiro: N:1 (Opcional - cada opcao pode ter UM roteiro)
 * - Menu inativo (ativo: false) nao e exibido para clientes
 * - Opcoes sao ordenadas pelo campo 'ordem'
 * - Se MenuOpcao.transfereDireto = true, pula roteiro e vai para atendente
 * - Se MenuOpcao.departamentoId nao existir, usa fallbackDepartamentoId do Menu
 * 
 * EXEMPLO PRATICO:
 * Menu: "Menu Principal" (canalId=1 - WhatsApp)
 *   ├── Opcao 1: titulo="Agendamento", departamentoId=3 (Agendamento Ambulatorial)
 *   ├── Opcao 2: titulo="Vendas", departamentoId=5 (Vendas)
 *   └── Opcao 3: titulo="Suporte", departamentoId=2 (Suporte)
 * 
 * Quando cliente seleciona "Agendamento":
 *   → Sistema busca usuarios do departamentoId=3
 *   → Direciona para usuarios com nivel de acesso para o departamento
 */
