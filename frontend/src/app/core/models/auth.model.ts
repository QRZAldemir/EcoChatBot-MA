export interface UsuarioLogado {
  id: number;
  nome: string;
  email: string;
  nivel?: string;
  departamentoId?: number;
  canalId?: number;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  usuario: UsuarioLogado;
}
