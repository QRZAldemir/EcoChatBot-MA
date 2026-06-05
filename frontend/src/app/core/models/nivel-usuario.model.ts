export type NivelAcesso = 'atendente' | 'supervisor' | 'gerente' | 'administrador';

export interface NivelUsuario {
  id: number;
  nome: string;
  codigo: NivelAcesso;
  descricao: string;
  permissoes: Permissao[];
  ativo: boolean;
}

export interface Permissao {
  modulo: string;
  leitura: boolean;
  escrita: boolean;
  exclusao: boolean;
}
