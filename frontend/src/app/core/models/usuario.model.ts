/**
 * EcoChatBot - Sistema de Atendimento
 * 
 * Arquivo: usuario.model.ts
 * Descricao: Define a interface para usuarios do sistema.
 * Este arquivo contem a estrutura de dados para gerenciamento de usuarios,
 * incluindo autenticacao, permissoes e associacoes a departamentos e canais.
 * 
 * Autor: Aldemir Querioz
 * Data: 2026-10-05
 * Versao: 2.0.0
 */

import { NivelAcesso } from './nivel-usuario.model';
import { Departamento } from './departamento.model';
import { Canal } from './canal.model';

/**
 * Usuario - Interface principal que representa um usuario do sistema
 * 
 * RELACIONAMENTOS:
 * - Departamento: Atraves de departamentoId (N:1) - Um usuario pertence a UM departamento
 * - Canal: Atraves de canalId (N:1) - Um usuario esta associado a UM canal
 * - Turno: Atraves de turno (N:1) - Um usuario pertence a UM turno
 * - Conexao: Atraves de conexao (N:1) - Um usuario pode estar associado a UM conexao
 * - NivelUsuario: Atraves de tipo/nivel (N:1) - Um usuario tem UM nivel de acesso
 * - Atendimento: Atraves de atendimento.usuarioId (1:N) - Um usuario pode ter varios atendimentos
 * - Campanha: Atraves de campanha.conexaoId -> Conexao (N:N) - Usuarios usam conexoes para campanhas
 * - UsuarioLogado: Versao simplificada para sessao (auth.model.ts)
 * 
 * DESCRICAO:
 * Representa um usuario do sistema com todas as suas configuracoes.
 * Usuarios podem ser atendentes, supervisores, gerentes ou administradores.
 * 
 * DESCRICAO DOS CAMPOS:
 * - id: Identificador unico do usuario (PK)
 * - nome: Nome completo do usuario
 * - usuario: Nome de usuario para login (username)
 * - email: Email do usuario para login e notificacoes
 * - senha: Senha do usuario (nao deve ser armazenada em plain text) - opcional
 * - depto: Nome do departamento (campo legado, preferir departamentoId) - opcional
 * - canal: Nome do canal (campo legado, preferir canalId) - opcional
 * - tipo: Tipo do usuario (TipoUsuario) - opcional
 * - nivel: Nivel de acesso (NivelAcesso) - opcional
 * - status: Status do usuario ('ativo' | 'inativo') - opcional
 * - conexao: Nome ou ID da conexao associada - opcional
 * - telefone: Telefone do usuario - opcional
 * - turno: ID ou nome do turno - opcional
 * - foto: URL ou caminho da foto do usuario - opcional
 * - data: Data de cadastro ou atualizacao - opcional
 * - criado_em: Data/hora de criacao (formato ISO, snake_case) - opcional
 * - departamentoId: FK para o departamento do usuario - opcional
 * - canalId: FK para o canal do usuario - opcional
 * - canalNome: Nome do canal associado - opcional
 * - canalArquivo: Caminho do arquivo do canal - opcional
 * 
 * TIPOS DE USUARIO:
 * - atendente: Atendente basico
 * - supervisor: Supervisor de atendentes
 * - gerente: Gerente do sistema
 * - administrador: Administrador do sistema
 * 
 * CAMPOS LEGADOS:
 * - depto: Use departamentoId em vez disso
 * - canal: Use canalId em vez disso
 * - conexao: Use conexaoId se disponivel
 * - data: Use criado_em em vez disso
 * 
 * USO NO PROJETO:
 * - Autenticacao e login
 * - Controle de acesso e permissoes
 * - Associacao a departamentos e canais
 * - Gerenciamento de atendentes
 */
export interface Usuario {
  id: number;
  nome: string;
  usuario: string;
  email: string;
  senha?: string;
  depto?: string;  // Campo legado, preferir departamentoId
  canal?: string;  // Campo legado, preferir canalId
  tipo?: 'atendente' | 'supervisor' | 'gerente' | 'administrador';
  nivel?: NivelAcesso;  // Tipo forte
  status?: 'ativo' | 'inativo';
  conexaoId?: number;  // Conexao associada - opcional (FK para conexao.id)
  telefone?: string;
  turnoId?: number;  // Turno associado - opcional (FK para turno.id)
  foto?: string;
  data?: string;  // Campo legado, preferir criado_em
  criado_em?: string;
  departamentoId?: Departamento['id'];
  canalId?: Canal['id'];
  canalNome?: string;
  canalArquivo?: string;
}

/**
 * TIPO_USUARIO - Array com os tipos de usuario possiveis
 * Usado para validacao e populacao de selects.
 */
export const TIPO_USUARIO: Array<'atendente' | 'supervisor' | 'gerente' | 'administrador'> = ['atendente', 'supervisor', 'gerente', 'administrador'];

/**
 * STATUS_USUARIO - Array com os status de usuario possiveis
 * Usado para validacao e populacao de selects.
 */
export const STATUS_USUARIO: Array<'ativo' | 'inativo'> = ['ativo', 'inativo'];

/**
 * MODELOS RELACIONADOS:
 * 
 * 1. NivelUsuario (nivel-usuario.model.ts)
 *    - NivelAcesso: type = 'atendente' | 'supervisor' | 'gerente' | 'administrador'
 *    - ... outros campos
 * 
 * 2. Departamento (departamento.model.ts)
 *    - id: number (PK)
 *    - nome: string
 *    - ... outros campos
 * 
 * 3. Canal (canal.model.ts)
 *    - id: number (PK)
 *    - nome: string
 *    - ... outros campos
 * 
 * 4. Turno (turno.model.ts)
 *    - id: number (PK)
 *    - desc: string
 *    - ... outros campos
 * 
 * 5. Conexao (conexao.model.ts)
 *    - id: number (PK)
 *    - nome: string
 *    - ... outros campos
 * 
 * REGRAS DE NEGOCIO:
 * - Usuario -> Departamento: N:1 (Muitos usuarios para um departamento)
 * - Usuario -> Canal: N:1 (Muitos usuarios para um canal)
 * - Usuario -> Turno: N:1 (Muitos usuarios para um turno)
 * - Usuario -> Conexao: N:1 (Muitos usuarios para uma conexao)
 * - Usuario -> Atendimento: 1:N (Um usuario pode ter varios atendimentos)
 * - Usuarios inativos (status: 'inativo') nao podem fazer login
 * - O nivel determina as permissoes do usuario
 * - O departamento e o canal determinam o escopo de acesso
 * - Cada usuario pode pertencer a apenas UM departamento, UM canal e UM turno
 */