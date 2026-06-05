import { NivelAcesso } from './nivel-usuario.model';

export interface Usuario {
  id: number;
  nome: string;
  email: string;
  telefone?: string;
  senha?: string;                 // nunca retornado pelo backend
  nivel: NivelAcesso;             // ex: 'atendente'
  departamentoId: number;
  departamentoNome?: string;      // populado em join
  canalId: number;
  canalNome?: string;             // populado em join
  canalArquivo?: string;          // ex: '1atendimento-mackenzie.html'
  status: 'ativo' | 'inativo';
  dataCadastro?: string;
  ultimoAcesso?: string;
}

// Exemplos de cadastro descritos pelo cliente:
// Aldemir   | nivel: atendente | depto: Call-Center  | canal: Exames-Diagnostico      → 3examesdiagnostico-mackenzie.html
// Ana       | nivel: atendente | depto: Call-Center  | canal: Atendimento-Cliente     → 1atendimento-mackenzie.html
// João      | nivel: atendente | depto: Recepção     | canal: Portaria                → 7portaria-mackenzie.html
// Francisca | nivel: atendente | depto: Ouvidoria    | canal: Ouvidoria               → 8ouvidoria-mackenzie.html
// Daniele   | nivel: atendente | depto: Call-Center  | canal: Agendamento-Ambulatorial→ 2agendamento-mackenzie.html
