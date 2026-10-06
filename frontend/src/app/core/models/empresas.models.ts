/**
 * EcoChatBot - Sistema de Atendimento
 * 
 * Arquivo: empresas.models.ts
 * Descricao: Define as interfaces e tipos relacionados a empresas e instancias.
 * Este arquivo contem as estruturas de dados para gerenciamento de empresas,
 * planos, instancias e validacoes do sistema multi-tenant.
 * 
 * NOTA IMPORTANTE:
 * - Empresa = Organizacao que contrata o sistema
 * - Instancia = Ambiente isolado para uma empresa
 * - Cada empresa pode ter N instancias
 * - Cada instancia pode ter N conexoes
 * - Cada instancia pertence a UMA empresa
 * 
 * Autor: Aldemir Querioz
 * Data: 2026-10-05
 * Versao: 2.0.0
 */

import { Conexao } from './conexao.model';
import { StatusConexao } from './conexao.model';

/**
 * PlanoEmpresa - Tipos de planos disponiveis para empresas
 * - starter: Plano basico
 * - pro: Plano profissional
 * - enterprise: Plano corporativo
 */
export type PlanoEmpresa = 'starter' | 'pro' | 'enterprise';

/**
 * Empresa - Interface principal que representa uma empresa
 * 
 * RELACIONAMENTOS:
 * - InstanciaResponseDto: Atraves de instancias (1:N) - Uma empresa pode ter varias instancias
 * - Conexao: Atraves de conexoes (1:N) - Uma empresa pode ter varias conexoes
 * - Usuario: Atraves de usuarios (1:N) - Uma empresa pode ter varios usuarios
 * 
 * DESCRICAO:
 * Representa uma empresa no sistema multi-tenant.
 * Contem informacoes de identificacao, contato e configuracoes do plano.
 * 
 * DESCRICAO DOS CAMPOS:
 * - id: Identificador unico da empresa (PK)
 * - nome: Nome da empresa
 * - cnpj_cpf: CNPJ ou CPF da empresa - opcional (pode ser null)
 * - email_contato: Email de contato da empresa
 * - telefone: Telefone da empresa - opcional (pode ser null)
 * - plano: Plano da empresa (PlanoEmpresa)
 * - max_instancias: Quantidade maxima de instancias permitidas
 * - ativo: Indica se a empresa esta ativa
 * - created_at: Data/hora de criacao (formato ISO, snake_case)
 * 
 * USO NO PROJETO:
 * - Gerenciamento de empresas no sistema multi-tenant
 * - Controle de limites de instancias por plano
 * - Associacao de usuarios a empresas
 */
export interface Empresa {
  id: number;
  nome: string;
  cnpj_cpf: string | null;
  email_contato: string;
  telefone: string | null;
  plano: PlanoEmpresa;
  max_instancias: number;
  ativo: boolean;
  created_at: string;
}

/**
 * EmpresaCreateDto - DTO para criacao de empresa
 * 
 * RELACIONAMENTOS:
 * - Empresa: Cria uma nova empresa com administrador
 * 
 * DESCRICAO:
 * DTO usado para criar uma nova empresa no sistema.
 * Inclui dados do administrador da empresa.
 * 
 * DESCRICAO DOS CAMPOS:
 * - nome: Nome da empresa (obrigatorio)
 * - cnpj_cpf: CNPJ ou CPF - opcional
 * - email_contato: Email de contato (obrigatorio)
 * - telefone: Telefone - opcional
 * - plano: Plano da empresa - opcional (default: 'starter')
 * - max_instancias: Maximo de instancias - opcional (default: 1)
 * - admin_nome: Nome do administrador (obrigatorio)
 * - admin_email: Email do administrador (obrigatorio)
 * - admin_senha: Senha do administrador (obrigatorio)
 * 
 * ENDPOINT DE USO:
 * - POST /empresas
 * - Body: EmpresaCreateDto
 * - Response: Empresa (com id gerado)
 */
export interface EmpresaCreateDto {
  nome: string;
  cnpj_cpf?: string;
  email_contato: string;
  telefone?: string;
  plano?: PlanoEmpresa;
  max_instancias?: number;
  admin_nome: string;
  admin_email: string;
  admin_senha: string;
}

/**
 * EmpresaUpdateDto - DTO para atualizacao de empresa
 * 
 * DESCRICAO:
 * DTO usado para atualizar configuracoes de uma empresa.
 * 
 * DESCRICAO DOS CAMPOS:
 * - plano: Novo plano da empresa - opcional
 * - max_instancias: Novo limite de instancias - opcional
 * - ativo: Novo status de ativa - opcional
 * 
 * ENDPOINT DE USO:
 * - PATCH /empresas/{id}
 * - Body: EmpresaUpdateDto
 * - Response: Empresa (atualizada)
 */
export interface EmpresaUpdateDto {
  plano?: PlanoEmpresa;
  max_instancias?: number;
  ativo?: boolean;
}

/**
 * InstanciaCreateDto - DTO para criacao de instancia
 * 
 * RELACIONAMENTOS:
 * - Empresa: Instancia pertence a uma empresa
 * - Conexao: Instancia pode ter conexoes associadas
 * 
 * DESCRICAO:
 * DTO usado para criar uma nova instancia para uma empresa.
 * 
 * DESCRICAO DOS CAMPOS:
 * - nome_instancia: Nome da instancia (obrigatorio)
 * - webhook_url: URL do webhook para notificacoes - opcional
 * 
 * ENDPOINT DE USO:
 * - POST /empresas/{empresaId}/instancias
 * - Body: InstanciaCreateDto
 * - Response: InstanciaResponseDto
 */
export interface InstanciaCreateDto {
  nome_instancia: string;
  webhook_url?: string;
}

/**
 * InstanciaResponseDto - Interface de resposta com dados da instancia
 * 
 * RELACIONAMENTOS:
 * - Empresa: Instancia pertence a uma empresa
 * - Conexao: Pode ter conexoes associadas
 * 
 * DESCRICAO:
 * Representa os dados de uma instancia retornados pela API.
 * 
 * DESCRICAO DOS CAMPOS:
 * - id: Identificador unico da instancia (PK)
 * - nome_instancia: Nome da instancia
 * - numero_whatsapp: Numero WhatsApp associado - opcional (pode ser null)
 * - status_conexao: Status da conexao (ex: 'conectada', 'desconectada')
 * - webhook_url: URL do webhook - opcional (pode ser null)
 * - ativo: Indica se a instancia esta ativa
 * - qrcode_base64: QR Code em base64 para autenticacao - opcional
 * 
 * USO NO PROJETO:
 * - Gerenciamento de instancias de empresas
 * - Associacao de numeros WhatsApp a instancias
 * - Monitoramento de status de conexao
 */
export interface InstanciaResponseDto {
  id: number;
  nome_instancia: string;
  numero_whatsapp: string | null;
  status_conexao: StatusConexao | string;  // Status de conexao ou string generico para retrocompatibilidade
  webhook_url: string | null;
  ativo: boolean;
  qrcode_base64?: string;
}

/**
 * VALIDACOES - Constantes centralizadas para validacao de dados
 * Usadas nos Validators do Angular para consistencia em todo o sistema.
 * 
 * VALIDACOES DE CAMPOS:
 * - nome: min 2, max 255 caracteres
 * - email: Formato de email valido
 * - senha: Minimo 6 caracteres
 * - nomeInstancia: 3-100 caracteres, apenas letras, numeros, hifens e underscores
 * - maxInstancias: Minimo 1
 */
export const VALIDACOES = {
  nome: { minLength: 2, maxLength: 255, msg: 'Nome deve ter entre 2 e 255 caracteres' },
  email: { msg: 'Formato de e-mail inválido' },
  senha: { minLength: 6, msg: 'Senha deve ter no mínimo 6 caracteres' },
  nomeInstancia: { 
    minLength: 3, 
    maxLength: 100, 
    pattern: /^[a-zA-Z0-9_\-]+$/, 
    msg: 'Apenas letras, números, hífens (-) e underscores (_) são permitidos (3 a 100 caracteres)' 
  },
  maxInstancias: { min: 1, msg: 'O mínimo permitido é 1' }
};

/**
 * MODELOS RELACIONADOS:
 * 
 * 1. Conexao (conexao.model.ts)
 *    - id: number (PK)
 *    - status: StatusConexao
 *    - ... outros campos
 * 
 * REGRAS DE NEGOCIO:
 * - Empresa -> InstanciaResponseDto: 1:N (Uma empresa pode ter varias instancias)
 * - Empresa -> Usuario: 1:N (Uma empresa pode ter varios usuarios)
 * - Empresa -> Conexao: 1:N (Uma empresa pode ter varias conexoes via instancias)
 * - Instancia -> Conexao: 1:N (Uma instancia pode ter varias conexoes)
 * - O plano determina o max_instancias
 * - Instancias inativas (ativo: false) nao processam mensagens
 */