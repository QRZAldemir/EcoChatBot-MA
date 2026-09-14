// ============================================================================
// MODELOS E CONSTANTES DE VALIDAÇÃO (Espelhando Pydantic do Backend)
// ============================================================================

export type PlanoEmpresa = 'starter' | 'pro' | 'enterprise';

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

export interface EmpresaUpdateDto {
  plano?: PlanoEmpresa;
  max_instancias?: number;
  ativo?: boolean;
}

export interface InstanciaCreateDto {
  nome_instancia: string;
  webhook_url?: string;
}

export interface InstanciaResponseDto {
  id: number;
  nome_instancia: string;
  numero_whatsapp: string | null;
  status_conexao: string;
  webhook_url: string | null;
  ativo: boolean;
  qrcode_base64?: string;
}

// Constantes centralizadas para uso nos Validators do Angular
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