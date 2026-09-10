export interface Usuario {
  id: number;
  nome: string;
  usuario: string;
  email: string;
  senha?: string;
  depto?: string;
  canal?: string;
  tipo?: 'atendente' | 'supervisor' | 'gerente' | 'administrador';
  nivel?: 'atendente' | 'supervisor' | 'gerente' | 'administrador';
  status?: 'ativo' | 'inativo';
  conexao?: string;
  telefone?: string;
  turno?: string;
  foto?: string;
  data?: string;
  criado_em?: string;
  departamentoId?: number;
  canalId?: number;
  canalNome?: string;
  canalArquivo?: string;
}

export const TIPO_USUARIO = ['atendente', 'supervisor', 'gerente', 'administrador'];
export const STATUS_USUARIO = ['ativo', 'inativo'];