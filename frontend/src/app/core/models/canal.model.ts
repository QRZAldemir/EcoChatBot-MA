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
  criadoEm?: string;
}

// Canais padrão do sistema Mackenzie
export const CANAIS_PADRAO: Partial<Canal>[] = [
  { nome: 'Atendimento-Cliente',          arquivoMenu: '1atendimento-ma.html',      icone: '📞', cor: '#2563eb' },
  { nome: 'Agendamento-Ambulatorial',     arquivoMenu: '2agendamento-ma.html',      icone: '📅', cor: '#f59e0b' },
  { nome: 'Exames-Diagnostico',           arquivoMenu: '3examesdiagnostico-ma.html',icone: '🩺', cor: '#22c55e' },
  { nome: 'Portaria',                     arquivoMenu: '7portaria-ma.html',         icone: '🚪', cor: '#c8102e' },
  { nome: 'Ouvidoria',                    arquivoMenu: '8ouvidoria-ma.html',        icone: '📢', cor: '#7c3aed' },
];
