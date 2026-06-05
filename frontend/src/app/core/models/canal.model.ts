export interface Canal {
  id: number;
  nome: string;
  descricao?: string;
  arquivoMenu: string;       // ex: "1atendimento-mackenzie.html"
  icone?: string;
  cor?: string;
  ativo: boolean;
  dataCriacao?: string;
}

// Canais padrão do sistema Mackenzie
export const CANAIS_PADRAO: Partial<Canal>[] = [
  { nome: 'Atendimento-Cliente',          arquivoMenu: '1atendimento-mackenzie.html',      icone: '📞', cor: '#2563eb' },
  { nome: 'Agendamento-Ambulatorial',     arquivoMenu: '2agendamento-mackenzie.html',      icone: '📅', cor: '#f59e0b' },
  { nome: 'Exames-Diagnostico',           arquivoMenu: '3examesdiagnostico-mackenzie.html',icone: '🩺', cor: '#22c55e' },
  { nome: 'Portaria',                     arquivoMenu: '7portaria-mackenzie.html',         icone: '🚪', cor: '#c8102e' },
  { nome: 'Ouvidoria',                    arquivoMenu: '8ouvidoria-mackenzie.html',        icone: '📢', cor: '#7c3aed' },
];
