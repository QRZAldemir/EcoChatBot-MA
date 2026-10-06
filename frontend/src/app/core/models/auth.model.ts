/**
 * EcoChatBot - Sistema de Atendimento
 * 
 * Arquivo: auth.model.ts
 * Descricao: Define as interfaces relacionadas ao modulo de autenticacao.
 * Este arquivo contem as estruturas de dados para gerenciamento de autenticacao,
 * sessao de usuarios e resposta da API de login.
 * 
 * Autor: Aldemir Querioz
 * Data: 2026-10-05
 * Versao: 2.0.0
 * 
 * NOTA SOBRE IMPORTS EM TYPESCRIPT:
 * - import { Tipo } from './arquivo' = Cria RELACIONAMENTO DE DEPENDENCIA
 * - O TypeScript usa o import para reutilizar tipos definidos em outros arquivos
 * - Isso NAO e relacionamento de banco de dados, mas SIM relacionamento de CODE DEPENDENCIA
 * - Se o tipo importado mudar, todos os arquivos que o importam serao atualizados
 */

import { NivelAcesso } from './nivel-usuario.model';
import { Departamento } from './departamento.model';
import { Canal } from './canal.model';

/**
 * UsuarioLogado - Interface que representa os dados do usuario autenticado
 * 
 * RELACIONAMENTOS:
 * - Departamento: Atraves de departamentoId (N:1) - Um usuario pertence a UM departamento
 * - Canal: Atraves de canalId (N:1) - Um usuario esta associado a UM canal
 * - NivelUsuario: Atraves de nivel (Usa tipo NivelAcesso para permissao)
 * 
 * DESCRICAO:
 * Contem as informacoes do usuario que esta atualmente logado no sistema.
 * Esses dados sao obtidos apos autenticacao bem-sucedida e sao armazenados
 * no estado da aplicacao para controle de sessao.
 * 
 * DESCRICAO DOS CAMPOS:
 * - id: Identificador unico do usuario (PK)
 * - nome: Nome completo do usuario
 * - email: Email do usuario para identificacao
 * - nivel: Nivel de permissao do usuario (NivelAcesso) - opcional
 * - departamentoId: FK para o departamento do usuario - opcional
 * - canalId: FK para o canal associado ao usuario - opcional
 * 
 * TIPO DE RELACIONAMENTO:
 * - IMPORT de NivelAcesso: Relacionamento de TIPO (TypeScript)
 * - departamentoId: Departamento['id']: Relacionamento de DADOS (FK)
 * - canalId: Canal['id']: Relacionamento de DADOS (FK)
 * 
 * USO NO PROJETO:
 * - Armazenamento de dados de sessao do usuario
 * - Controle de acesso e permissao
 * - Exibicao de informacoes do usuario na interface
 */
export interface UsuarioLogado {
  id: number;
  nome: string;
  email: string;
  nivel?: NivelAcesso;  // Importado de nivel-usuario.model.ts
  departamentoId?: Departamento['id'];  // Tipo do ID de Departamento
  canalId?: Canal['id'];  // Tipo do ID de Canal
}

/**
 * LoginResponse - Interface que representa a resposta da API de autenticacao
 * 
 * RELACIONAMENTOS:
 * - UsuarioLogado: Contem um objeto UsuarioLogado com os dados do usuario
 * 
 * DESCRICAO:
 * Estrutura de dados retornada pelo endpoint de login da API.
 * Contem o token de acesso e as informacoes do usuario autenticado.
 * 
 * DESCRICAO DOS CAMPOS:
 * - access_token: Token JWT para autenticacao em requisicoes subsequentes
 * - token_type: Tipo do token (normalmente 'Bearer')
 * - usuario: Objeto UsuarioLogado com os dados do usuario autenticado
 * 
 * USO NO PROJETO:
 * - Recepcao da resposta do endpoint POST /auth/login
 * - Armazenamento do token para requisicoes autenticadas
 * - Inicializacao da sessao do usuario no frontend
 */
export interface LoginResponse {
  access_token: string;
  token_type: 'Bearer';  // Tipo literal, nao string generico
  usuario: UsuarioLogado;
}

/**
 * MODELOS RELACIONADOS (para referencia):
 * 
 * 1. NivelUsuario (nivel-usuario.model.ts)
 *    - NivelAcesso: type = 'atendente' | 'supervisor' | 'gerente' | 'administrador'
 *    - NivelUsuario: interface com permissoes detalhadas
 *    
 * 2. Departamento (departamento.model.ts)
 *    - id: number (PK)
 *    - nome: string
 *    - descricao?: string
 *    - status?: 'ativo' | 'inativo'
 *    
 * 3. Canal (canal.model.ts)
 *    - id: number (PK)
 *    - nome: string
 *    - descricao?: string
 *    - arquivoMenu: string
 *    - tipo: 'whatsapp' | 'telegram' | 'email'
 *    
 * 4. Usuario (usuario.model.ts)
 *    - id: number (PK)
 *    - nome: string
 *    - email: string
 *    - tipo?: 'atendente' | 'supervisor' | 'gerente' | 'administrador'
 *    - nivel?: NivelAcesso
 *    - status?: 'ativo' | 'inativo'
 *    - departamentoId?: Departamento['id']
 *    - canalId?: Canal['id']
 * 
 * REGRAS DE NEGOCIO:
 * - UsuarioLogado -> Departamento: N:1 (Muitos usuarios para um departamento)
 * - UsuarioLogado -> Canal: N:1 (Muitos usuarios para um canal)
 * - Um usuario so pode estar logado em UM departamento e UM canal por vez
 * 
 * FLUXO DE AUTENTICACAO:
 * 1. Usuario envia credenciais (email/senha) para POST /auth/login
 * 2. API retorna LoginResponse com access_token e usuario
 * 3. Frontend armazena token e dados do usuario (UsuarioLogado)
 * 4. Token e usado em headers de requisicoes autenticadas
 * 5. Dados do UsuarioLogado sao usados para controle de sessao e permissao
 * 
 * NOTA TECNICA:
 * - Os IMPORTS criam DEPENDENCIA entre os arquivos
 * - Se nivel-usuario.model.ts, departamento.model.ts ou canal.model.ts mudarem,
 *   este arquivo pode precisar de ajustes
 * - Isso e bom: garante consistencia em todo o sistema
 */
