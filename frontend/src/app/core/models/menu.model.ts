export interface MenuOpcao {
  id?: number;
  menuId?: number;
  titulo: string;
  descricao?: string;
  rowId: string;
  ordem: number;
}

export interface Menu {
  id: number;
  titulo: string;
  descricao?: string;
  rodape?: string;
  textoBotao: string;
  canalId?: number;
  canalNome?: string;
  ativo: boolean;
  criadoEm?: string;
  opcoes: MenuOpcao[];
}
