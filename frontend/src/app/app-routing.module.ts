// ╔══════════════════════════════════════════════════════════════════════════════╗
// ║  PROJETO.......: EcoChatBotMarcx — Sistema de Atendimento Digital          ║
// ║  ARQUIVO.......: app-routing.module.ts                                     ║
// ║  LOCALIZAÇÃO...: Frontend/App/app-routing.module.ts                        ║
// ║  AUTOR.........: Ademir Queiroz                                            ║
// ║  DATA..........: 08/09/2026                                                ║
// ║  VERSÃO........: 1.0.0                                                     ║
// ║                                                                            ║
// ║  DESCRIÇÃO                                                                 ║
// ║  Módulo de rotas da aplicação Angular (padrão NgModule).                   ║
// ║  Responsável por definir o "mapa de navegação" do sistema — quais URLs     ║
// ║  são válidas e qual componente deve ser renderizado em cada uma.           ║
// ║                                                                            ║
// ║  CONCEITO-CHAVE: LAZY LOADING                                              ║
// ║  A função loadChildren() carrega o módulo SOMENTE quando o usuário         ║
// ║  acessa a rota correspondente. Isso reduz o tamanho do bundle inicial      ║
// ║  e melhora o tempo de carregamento da aplicação.                           ║
// ║                                                                            ║
// ║  OBSERVAÇÃO                                                                ║
// ║  Este arquivo coexiste com app.routes.ts (padrão standalone moderno).      ║
// ║  Recomenda-se migrar completamente para o padrão standalone (Angular 17+). ║
// ╚══════════════════════════════════════════════════════════════════════════════╝

// ─────────────────────────────────────────────────────────────────────────────
// IMPORTAÇÕES
// ─────────────────────────────────────────────────────────────────────────────
// No Angular, "import" segue o padrão ES Modules (ECMAScript 2015+).
// Cada linha importa um ou mais símbolos (classes, funções, tipos) de um
// pacote ou arquivo local. O caminho './...' indica arquivo do próprio projeto.
// ─────────────────────────────────────────────────────────────────────────────
import { NgModule } from '@angular/core';
//   NgModule → decorator (função especial com sintaxe @Nome) que marca a classe
//              como um módulo Angular. Um módulo agrupa componentes, diretivas,
//              pipes e serviços relacionados, funcionando como uma "unit"
//              organizada do sistema.

import { RouterModule, Routes } from '@angular/router';
//   RouterModule → módulo que fornece toda a infraestrutura de navegação:
//                    • forRoot(routes)  → registra rotas globais (raiz)
//                    • forChild(routes) → registra rotas em módulos filhos
//                    • <router-outlet>  → diretiva que marca o ponto de injeção
//                    • [routerLink]     → diretiva que cria links de navegação
//                    • ActivatedRoute   → serviço com informações da rota ativa
//
//   Routes → interface TypeScript que define o formato do array de rotas.
//            Usada apenas para tipagem — o compilador valida a estrutura.


// ─────────────────────────────────────────────────────────────────────────────
// DEFINIÇÃO DAS ROTAS
// ─────────────────────────────────────────────────────────────────────────────
// O array "routes" contém objetos que descrevem cada regra de navegação.
//
// PROPRIEDADES DISPONÍVEIS EM CADA ROTA:
//   path          → trecho da URL (sem a barra inicial)
//   component     → componente a ser renderizado (uso direto)
//   loadChildren  → função que carrega módulo filho sob demanda (lazy loading)
//   redirectTo    → URL de destino para redirecionamento
//   pathMatch     → estratégia de correspondência ('prefix' ou 'full')
//   canActivate   → array de guards (verificações antes de ativar a rota)
//   children      → rotas filhas (aninhadas dentro desta)
//   title         → título da página (exibido na aba do navegador)
//
// ORDEM DE AVALIAÇÃO:
//   O Angular percorre o array de cima para baixo. A PRIMEIRA rota que casar
//   com a URL é a vencedora. Por isso, rotas específicas vêm antes das genéricas.
// ─────────────────────────────────────────────────────────────────────────────
const routes: Routes = [

  // ── ROTA RAIZ ───────────────────────────────────────────────────────────
  // URL: http://dominio/ (vazia)
  // Ação: redireciona para /admin/dashboard
  //
  // pathMatch: 'full' → exige que a URL seja EXATAMENTE '' (vazia).
  // Se fosse 'prefix' (padrão), casaria com qualquer URL que COMEÇE com ''.
  {
    path: '',
    redirectTo: '/admin/dashboard',
    pathMatch: 'full'
  },

  // ── MÓDULO ADMIN ────────────────────────────────────────────────────────
  // URL: http://dominio/admin/*
  // Ação: carrega o módulo de rotas admin sob demanda
  //
  // loadChildren → função que retorna uma Promise do módulo.
  //   import() → função nativa do JavaScript para importação dinâmica.
  //              Retorna uma Promise que resolve para o módulo carregado.
  //   .then(m => m.ADMIN_ROUTES) → extrai a constante ADMIN_ROUTES exportada
  //                                do arquivo admin.routes.ts.
  {
    path: 'admin',
    loadChildren: () =>
      import('./pages/admin/admin.routes')
        .then(m => m.ADMIN_ROUTES)
  },

  // ── MÓDULO USUÁRIOS (padrão NgModule) ───────────────────────────────────
  // URL: http://dominio/usuarios/*
  // Carrega o módulo UsuariosModule (padrão antigo com @NgModule).
  {
    path: 'usuarios',
    loadChildren: () =>
      import('./modules/usuarios/usuarios.module')
        .then(m => m.UsuariosModule)
  },

  // ── MÓDULO TURNOS (padrão NgModule) ─────────────────────────────────────
  // URL: http://dominio/turnos/*
  // Carrega o módulo TurnosModule (padrão antigo com @NgModule).
  {
    path: 'turnos',
    loadChildren: () =>
      import('./modules/turnos/turnos.module')
        .then(m => m.TurnosModule)
  },

  // ── WILDCARD (catch-all) ────────────────────────────────────────────────
  // path: '**' → casa com QUALQUER URL não mapeada anteriormente.
  // SEMPRE deve ser a última rota do array.
  //
  // Função: evita tela 404 em branco — redireciona para o dashboard.
  {
    path: '**',
    redirectTo: '/admin/dashboard'
  }
];


// ─────────────────────────────────────────────────────────────────────────────
// DECORATOR @NgModule
// ─────────────────────────────────────────────────────────────────────────────
// O @NgModule organiza a aplicação em blocos coesos.
//
// PROPRIEDADES DO @NgModule:
//   declarations → componentes, diretivas e pipes PERTENCENTES a este módulo
//   imports      → outros módulos que este módulo UTILIZA
//   exports      → o que este módulo DISPONIBILIZA para outros módulos
//   providers    → serviços registrados no injetor de dependência
//   bootstrap    → componente raiz (apenas no módulo principal)
//
// NO CASO DESTE MÓDULO:
//   imports  → RouterModule.forRoot(routes) → registra as rotas globalmente
//   exports  → RouterModule → torna <router-outlet> e [routerLink] disponíveis
//
// forRoot() vs forChild():
//   forRoot()  → usado UMA VEZ na aplicação (módulo raiz).
//                Registra serviços singleton (roteador, localização).
//   forChild() → usado em módulos filhos.
//                NÃO registra os serviços novamente (apenas as rotas).
// ─────────────────────────────────────────────────────────────────────────────
@NgModule({
  imports: [RouterModule.forRoot(routes)],   // Registra rotas globais
  exports: [RouterModule]                    // Disponibiliza <router-outlet> e [routerLink]
})
export class AppRoutingModule { }
//   export    → torna a classe acessível para importação em outros arquivos
//   class     → declaração de classe TypeScript (estrutura de dados + métodos)
//   { }       → corpo da classe (vazio neste caso, pois o módulo só configura rotas)