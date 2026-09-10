export type CorOpcao = 'verde' | 'azul' | 'vermelho' | 'amarelo' | 'roxo' | 'cinza';

export const CORES_OPCAO: CorOpcao[] = ['verde', 'azul', 'vermelho', 'amarelo', 'roxo', 'cinza'];

export interface MenuOpcao {
  id?: number;
  menuId?: number;
  titulo: string;
  descricao?: string;
  rowId: string;
  ordem: number;
  cor?: CorOpcao;
}

export interface Menu {
  id: number;
  titulo: string;
  descricao?: string;
  cabecalho?: string;
  rodape?: string;
  textoBotao: string;
  canalId?: number;
  canalNome?: string;
  usuarioVinculadoId?: number;
  usuarioVinculadoNome?: string;
  ativo: boolean;
  criadoEm?: string;
  opcoes: MenuOpcao[];
}
