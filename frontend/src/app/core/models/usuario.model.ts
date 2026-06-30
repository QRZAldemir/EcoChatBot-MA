import { NivelAcesso } from './nivel-usuario.model';

export interface Usuario {
  id: number;
  nome: string;
  email: string;
  telefone?: string;
  senha?: string;                 // nunca retornado pelo backend
  nivel: NivelAcesso;             // ex: 'atendente'
  nivel_id?: number;              // FK raw do backend
  departamentoId?: number;
  departamento_id?: number;       // FK raw do backend
  departamentoNome?: string;
  canalId?: number;
  canal_id?: number;              // FK raw do backend
  canalNome?: string;
  canalArquivo?: string;
  ativo: boolean;                 // campo real do backend
  status: 'ativo' | 'inativo';   // normalizado pelo UsuarioService
  criado_em?: string;
  atualizado_em?: string;
}

// Exemplos de cadastro descritos pelo cliente:
// Aldemir   | nivel: atendente | depto: Call-Center  | canal: Exames-Diagnostico      → 3examesdiagnostico-ma.html
// Ana       | nivel: atendente | depto: Call-Center  | canal: Atendimento-Cliente     → 1atendimento-ma.html
// João      | nivel: atendente | depto: Recepção     | canal: Portaria                → 7portaria-ma.html
// Francisca | nivel: atendente | depto: Ouvidoria    | canal: Ouvidoria               → 8ouvidoria-ma.html
// Daniele   | nivel: atendente | depto: Call-Center  | canal: Agendamento-Ambulatorial→ 2agendamento-ma.html
