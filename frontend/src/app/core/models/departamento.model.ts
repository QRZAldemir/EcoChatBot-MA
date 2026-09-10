export interface Departamento {
  id: number;
  nome: string;
  descricao?: string;
  desc?: string;
  ativo?: boolean;
  status?: 'ativo' | 'inativo';
  criado_em?: string;
}