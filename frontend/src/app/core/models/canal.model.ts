export interface Canal {
  id: number;
  nome: string;
  descricao?: string;
  // O backend retorna snake_case; o serviço normaliza para camelCase
  arquivoMenu: string;       // ex: "1atendimento-ma.html"
  arquivo_menu?: string;     // campo raw do backend (fallback)
  icone?: string;            // campo local — não existe no backend, populado pelo frontend
  cor?: string;              // campo local — não existe no backend
  departamentoId?: number;
  departamentoNome?: string;
  ativo: boolean;
  status?: 'ativo' | 'inativo';
  criadoEm?: string;
}

// Exemplos neutros usados apenas quando o modo local precisa de dados iniciais.
export const CANAIS_PADRAO: Partial<Canal>[] = [
  { nome: 'Atendimento Geral', arquivoMenu: '', icone: '💬', cor: '#2563eb' },
  { nome: 'Vendas', arquivoMenu: '', icone: '🛍️', cor: '#f59e0b' },
  { nome: 'Suporte', arquivoMenu: '', icone: '🛠️', cor: '#22c55e' },
  { nome: 'Financeiro', arquivoMenu: '', icone: '💳', cor: '#0f766e' },
  { nome: 'Feedback', arquivoMenu: '', icone: '📢', cor: '#7c3aed' },
];
