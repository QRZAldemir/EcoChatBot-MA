# EcoChatBotMarcx — Documentação Técnica do Frontend

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Estrutura de Arquivos](#estrutura-de-arquivos)
3. [Arquivo 1: app-routing.module.ts](#arquivo-1-app-routingmodulets)
4. [Arquivo 2: app.component.html](#arquivo-2-appcomponenthtml)
5. [Arquivo 3: app.component.scss](#arquivo-3-appcomponentscss)
6. [Arquivo 4: app.component.ts](#arquivo-4-appcomponentts)
7. [Arquivo 5: app.routes.ts](#arquivo-5-approutests)
8. [Guia de Instalação e Uso](#guia-de-instalação-e-uso)
9. [Solução de Problemas](#solução-de-problemas)
10. [Arquitetura do Sistema](#arquitetura-do-sistema)

---

## Visão Geral

O **EcoChatBotMarcx** é um sistema de atendimento digital configurável, desenvolvido com **Angular 17+** no frontend e **FastAPI (Python)** no backend.

### Características Principais

- 🏗️ **Arquitetura moderna** — Componentes standalone (Angular 17+)
- 🔒 **Autenticação** — Rotas protegidas com `authGuard`
- ⚡ **Lazy Loading** — Carregamento sob demanda para otimização
- 🎨 **SCSS com variáveis** — Tema centralizado e facilmente customizável
- 📱 **Responsivo** — Layout com Flexbox
- 🧩 **Configurável** — Departamentos, canais e roteiros cadastráveis

### Tecnologias Utilizadas

| Tecnologia | Versão | Finalidade |
|------------|--------|------------|
| Angular | 17+ | Framework frontend |
| TypeScript | 5.4+ | Linguagem de programação |
| SCSS | - | Pré-processador CSS |
| RxJS | 7+ | Programação reativa |
| Font Awesome | 6+ | Ícones |

---

## Estrutura de Arquivos

### Localização dos Arquivos

Todos os arquivos documentados estão na pasta:

# EcoChatBotMarcx — Documentação Técnica do Frontend

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Estrutura de Arquivos](#estrutura-de-arquivos)
3. [Arquivo 1: app-routing.module.ts](#arquivo-1-app-routingmodulets)
4. [Arquivo 2: app.component.html](#arquivo-2-appcomponenthtml)
5. [Arquivo 3: app.component.scss](#arquivo-3-appcomponentscss)
6. [Arquivo 4: app.component.ts](#arquivo-4-appcomponentts)
7. [Arquivo 5: app.routes.ts](#arquivo-5-approutests)
8. [Guia de Instalação e Uso](#guia-de-instalação-e-uso)
9. [Solução de Problemas](#solução-de-problemas)
10. [Arquitetura do Sistema](#arquitetura-do-sistema)

---

## Visão Geral

O **EcoChatBotMarcx** é um sistema de atendimento digital configurável, desenvolvido com **Angular 17+** no frontend e **FastAPI (Python)** no backend.

### Características Principais

- 🏗️ **Arquitetura moderna** — Componentes standalone (Angular 17+)
- 🔒 **Autenticação** — Rotas protegidas com `authGuard`
- ⚡ **Lazy Loading** — Carregamento sob demanda para otimização
- 🎨 **SCSS com variáveis** — Tema centralizado e facilmente customizável
- 📱 **Responsivo** — Layout com Flexbox
- 🧩 **Configurável** — Departamentos, canais e roteiros cadastráveis

### Tecnologias Utilizadas

| Tecnologia | Versão | Finalidade |
|------------|--------|------------|
| Angular | 17+ | Framework frontend |
| TypeScript | 5.4+ | Linguagem de programação |
| SCSS | - | Pré-processador CSS |
| RxJS | 7+ | Programação reativa |
| Font Awesome | 6+ | Ícones |

---

## Estrutura de Arquivos

### Localização dos Arquivos

Todos os arquivos documentados estão na pasta:


### Relacionamento entre Arquivos
─────────────────────────────────────────────────────────────────────┐
│ main.ts │
│ ┌──────────────────────────────────────────────────────────────┐ │
│ │ bootstrapApplication(AppComponent) │ │
│ │ ou │ │
│ │ platformBrowserDynamic().bootstrapModule(AppModule) │ │
│ └──────────────────────────────────────────────────────────────┘ │
│ │ │
│ ▼ │
│ ┌──────────────────────────────────────────────────────────────┐ │
│ │ app.component.ts │ │
│ │ selector: 'app-root' standalone: true │ │
│ │ imports: [CommonModule, RouterOutlet, SidebarComponent] │ │
│ │ templateUrl: './app.component.html' │ │
│ │ styleUrls: ['./app.component.scss'] │ │
│ └──────────────────────────────────────────────────────────────┘ │
│ │ │ │ │
│ ▼ ▼ ▼ │
│ app.component.html app.component.scss app.routes.ts │
│ (template visual) (estilos) (configuração de rotas) │
│ (standalone) │
│ │
│ ┌──────────────────────────────────────────────────────────────┐ │
│ │ app-routing.module.ts │ │
│ │ (alternativa legada — compatibilidade com NgModules) │ │
│ └──────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘

---

## Arquivo 1: app-routing.module.ts

### Visão Geral

Módulo de rotas da aplicação Angular no **padrão NgModule** (legado). Define o mapa de navegação do sistema e utiliza **lazy loading** para carregar módulos sob demanda.

### Código

```typescript
import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

const routes: Routes = [
  {
    path: '',
    redirectTo: '/admin/dashboard',
    pathMatch: 'full'
  },
  {
    path: 'admin',
    loadChildren: () =>
      import('./pages/admin/admin.routes')
        .then(m => m.ADMIN_ROUTES)
  },
  {
    path: 'usuarios',
    loadChildren: () =>
      import('./modules/usuarios/usuarios.module')
        .then(m => m.UsuariosModule)
  },
  {
    path: 'turnos',
    loadChildren: () =>
      import('./modules/turnos/turnos.module')
        .then(m => m.TurnosModule)
  },
  {
    path: '**',
    redirectTo: '/admin/dashboard'
  }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }

Explicação das Propriedades
Propriedade	Descrição
path: ''	Rota raiz da aplicação (URL vazia)
redirectTo	Para onde redirecionar o usuário
pathMatch: 'full'	Exige correspondência exata da URL
loadChildren	Carrega módulo filho sob demanda (lazy loading)
import()	Importação dinâmica do ES2020
.then(m => m.ADMIN_ROUTES)	Extrai a constante exportada do módulo
path: '**'	Wildcard — captura qualquer URL não mapeada
@NgModule	Decorator que define a classe como módulo Angular

URL acessada                    → Ação
─────────────────────────────────────────────────────────
http://dominio/                 → redireciona para /admin/dashboard
http://dominio/admin/*          → carrega admin.routes (lazy)
http://dominio/usuarios/*       → carrega UsuariosModule (lazy)
http://dominio/turnos/*         → carrega TurnosModule (lazy)
http://dominio/qualquer-outra   → redireciona para /admin/dashboard

⚠️ Observação Importante

Este arquivo é legado (padrão NgModule). O projeto também possui app.routes.ts (padrão standalone moderno). Recomenda-se migrar completamente para o padrão standalone no futuro.


Arquivo 2: app.component.html
Visão Geral

Template raiz da aplicação. Define o layout global composto por:

    Barra lateral de navegação (sidebar)

    Barra superior fixa (topbar)

    Área de conteúdo dinâmico (router-outlet)

Código
<div class="app-container">

  <!-- SIDEBAR — Barra lateral de navegação -->
  <app-sidebar></app-sidebar>

  <!-- ÁREA PRINCIPAL -->
  <div class="main">

    <!-- TOPBAR — Barra superior fixa -->
    <div class="topbar">
      <div class="tb-title">
        <i class="fas fa-users" style="color:var(--red);margin-right:8px"></i>
        Cadastro de <span>Usuários</span>
      </div>
      <button class="tb-btn" title="Atualizar" (click)="reload()">
        <i class="fas fa-rotate-right"></i>
      </button>
    </div>

    <!-- CONTEÚDO DINÂMICO -->
    <div class="content">
      <router-outlet></router-outlet>
    </div>

  </div>
</div>

Elementos do Template
Elemento	Tipo	Descrição
<app-sidebar>	Componente	Barra lateral com menu de navegação
.app-container	Contêiner	Envolve toda a aplicação (layout flex)
.main	Contêiner	Área principal à direita da sidebar
.topbar	Contêiner	Barra superior fixa com título e ações
.tb-title	Título	Exibe o título da tela atual
<i class="fas fa-users">	Ícone	Ícone FontAwesome de "usuários"
<span>Usuários</span>	Destaque	Texto com cor vermelha do tema
.tb-btn	Botão	Botão de atualização
(click)="reload()"	Event Binding	Chama método reload() ao clicar
.content	Contêiner	Área que envolve o router-outlet
<router-outlet>	Diretiva	Ponto de injeção do componente ativo

Conceitos Angular Utilizados
Conceito	Sintaxe	Descrição
Event Binding	(click)="reload()"	Vincula evento DOM a método do componente
Interpolação	{{ title }}	Exibe valor da propriedade no template
Property Binding	[title]="valor"	Vincula propriedade do elemento a valor
Diretiva	*ngIf, *ngFor	Estruturas condicionais e de repetição

Fluxo de Renderização

1. index.html carrega <app-root>
2. Angular renderiza app.component.html
3. <app-sidebar> é renderizado (menu lateral)
4. <router-outlet> injeta o componente da rota ativa
5. O componente filho herda o layout (sidebar + topbar)

Arquivo 3: app.component.scss
Visão Geral

Folha de estilos do componente raiz. Utiliza SCSS (Sassy CSS) com:

    Variáveis (via import de arquivo externo)

    Aninhamento de seletores (nesting)

    Estilos globais reutilizáveis via ::ng-deep
 
 Código
 @import '../assets/styles/variables';

.app-container {
  display: flex;
  min-height: 100vh;
  font-family: var(--font);
  font-size: 13.5px;
}

.main {
  margin-left: 248px;
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.topbar {
  height: 52px;
  background: var(--card);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  padding: 0 20px;
  gap: 12px;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);

  .tb-title {
    font-size: 14px;
    font-weight: 700;
    flex: 1;

    span {
      color: var(--red);
    }
  }

  .tb-btn {
    width: 32px;
    height: 32px;
    border-radius: 8px;
    border: 1.5px solid var(--border);
    background: none;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--muted);
    font-size: 13px;
    transition: 0.14s;

    &:hover {
      border-color: var(--red);
      color: var(--red);
    }
  }
}

.content {
  padding: 20px;
  flex: 1;
}

.req {
  color: var(--red);
}

:host ::ng-deep {
  .card {
    background: var(--card);
    border-radius: var(--r);
    border: 1px solid var(--border);
    box-shadow: var(--sh);
    overflow: hidden;
    margin-bottom: 16px;
  }

  .card-hd {
    padding: 11px 16px;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    gap: 8px;

    h3 {
      font-size: 12.5px;
      font-weight: 700;
      flex: 1;
    }
  }

  .btn {
    padding: 7px 16px;
    border-radius: 8px;
    border: none;
    cursor: pointer;
    font-family: var(--font);
    font-size: 12px;
    font-weight: 600;
    transition: 0.14s;
    display: inline-flex;
    align-items: center;
    gap: 5px;

    &.p {
      background: var(--red);
      color: #fff;

      &:hover {
        background: var(--red-dark);
      }
    }

    &.s {
      background: var(--card);
      color: var(--text);
      border: 1.5px solid var(--border);

      &:hover {
        border-color: var(--red);
        color: var(--red);
      }
    }

    &.sm {
      padding: 4px 9px;
      font-size: 11px;
    }
  }
}

Variáveis CSS Utilizadas
Variável	Descrição	Valores Típicos
--font	Família da fonte	'Segoe UI', sans-serif
--card	Cor de fundo do card	#ffffff
--border	Cor das bordas	#e2e8f0
--red	Cor primária (vermelho)	#dc2626
--red-dark	Cor primária escura	#b91c1c
--text	Cor do texto principal	#1a202c
--muted	Cor do texto secundário	#a0aec0
--r	Raio de borda padrão	8px
--sh	Sombra padrão	0 1px 3px rgba(0,0,0,0.06)
Classes Reutilizáveis
Classe	Descrição	Exemplo de Uso
.card	Container visual com borda e sombra	<div class="card">
.card-hd	Cabeçalho do card	<div class="card-hd">
.btn	Botão base	<button class="btn">
.btn.p	Botão primário (vermelho)	<button class="btn p">Salvar</button>
.btn.s	Botão secundário	<button class="btn s">Cancelar</button>
.btn.sm	Botão pequeno	<button class="btn sm">Ok</button>
.req	Campo obrigatório	<span class="req">*</span>
Conceitos SCSS
Conceito	Sintaxe	Descrição
Import	@import 'caminho'	Importa outro arquivo SCSS
Variável CSS	var(--nome)	Acessa variável CSS customizada
Aninhamento	.pai { .filho { } }	Seletor filho dentro do pai
Referência pai	&	Representa o seletor pai (ex: &:hover)
Pseudo-classe	&:hover	Estado ao passar o mouse
⚠️ Observação sobre ::ng-deep

O ::ng-deep desativa o encapsulamento de escopo do Angular, permitindo que estilos definidos aqui vazem para componentes filhos. As classes .card e .btn são reutilizadas em toda a aplicação.

Alternativa moderna: Criar um arquivo styles.scss global na raiz do projeto.

Arquivo 4: app.component.ts
Visão Geral

Componente raiz da aplicação Angular. É o ponto de entrada visual e lógico do sistema.

Código
import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet } from '@angular/router';
import { SidebarComponent } from './shared/components/sidebar/sidebar.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet, SidebarComponent],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent {
  title = 'EcoChat Marcx';

  reload(): void {
    window.location.reload();
  }
}

Propriedades do @Component
Propriedade	Valor	Descrição
selector	'app-root'	Tag HTML customizada usada em index.html
standalone	true	Modo moderno (dispensa NgModule)
imports	[...]	Dependências usadas no template
templateUrl	'./app.component.html'	Arquivo HTML do template
styleUrls	['./app.component.scss']	Arquivos de estilo
Propriedades e Métodos
Nome	Tipo	Descrição
title	string	Título da aplicação (EcoChat Marcx)
reload()	void	Recarrega a página inteira

Ciclo de Vida
1. main.ts inicializa a aplicação
2. AppComponent é instanciado (UMA VEZ)
3. Template (app.component.html) é renderizado
4. Componente permanece ativo durante toda a sessão
5. O usuário interage com a aplicação

Arquivo 5: app.routes.ts
Visão Geral

Configuração moderna de rotas usando o padrão standalone do Angular 17+. É a alternativa atualizada ao app-routing.module.ts.
Código
import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';

export const routes: Routes = [
  { path: '', redirectTo: 'admin/dashboard', pathMatch: 'full' },

  // LOGIN — Rota pública
  {
    path: 'login',
    loadComponent: () =>
      import('./pages/login/login.component').then(m => m.LoginComponent),
    title: 'Login — EcoChatBotMarcx'
  },

  // ADMIN — Rotas protegidas
  {
    path: 'admin',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./shared/components/admin-layout/admin-layout.component')
        .then(m => m.AdminLayoutComponent),
    children: [
      {
        path: 'dashboard',
        loadComponent: () =>
          import('./pages/admin/dashboard/dashboard.component')
            .then(m => m.DashboardComponent),
        title: 'Dashboard — EcoChatBotMarcx'
      },
      {
        path: 'atendimentos',
        loadComponent: () =>
          import('./pages/admin/atendimentos/atendimentos.component')
            .then(m => m.AtendimentosComponent),
        title: 'Atendimentos — EcoChatBotMarcx'
      },
      {
        path: 'usuarios',
        loadComponent: () =>
          import('./pages/admin/usuarios/usuarios.component')
            .then(m => m.UsuariosComponent),
        title: 'Usuários — EcoChatBotMarcx'
      },
      {
        path: 'departamentos',
        loadComponent: () =>
          import('./pages/admin/departamentos/departamentos.component')
            .then(m => m.DepartamentosComponent),
        title: 'Departamentos — EcoChatBotMarcx'
      },
      {
        path: 'canais',
        loadComponent: () =>
          import('./pages/admin/canais/canais.component')
            .then(m => m.CanaisComponent),
        title: 'Canais de Atendimento — EcoChatBotMarcx'
      },
      {
        path: 'conexoes',
        loadComponent: () =>
          import('./pages/admin/conexoes/conexoes.component')
            .then(m => m.ConexoesComponent),
        title: 'Conexões — EcoChatBotMarcx'
      },
      {
        path: 'contatos',
        loadComponent: () =>
          import('./pages/admin/contatos/contatos.component')
            .then(m => m.ContatosComponent),
        title: 'Contatos — EcoChatBotMarcx'
      },
      {
        path: 'email',
        loadComponent: () =>
          import('./pages/admin/email/email.component')
            .then(m => m.EmailComponent),
        title: 'E-mail — EcoChatBotMarcx'
      },
      {
        path: 'campanhas',
        loadComponent: () =>
          import('./pages/admin/campanhas/campanhas.component')
            .then(m => m.CampanhasComponent),
        title: 'Campanhas — EcoChatBotMarcx'
      },
      {
        path: 'arquivos',
        loadComponent: () =>
          import('./pages/admin/arquivos/arquivos.component')
            .then(m => m.ArquivosComponent),
        title: 'Arquivos — EcoChatBotMarcx'
      },
      {
        path: 'mensagens',
        loadComponent: () =>
          import('./pages/admin/mensagens/mensagens.component')
            .then(m => m.MensagensComponent),
        title: 'Mensagens — EcoChatBotMarcx'
      },
      {
        path: 'niveis',
        loadComponent: () =>
          import('./pages/admin/niveis/niveis.component')
            .then(m => m.NiveisComponent),
        title: 'Níveis de Usuário — EcoChatBotMarcx'
      },
      {
        path: 'escalas',
        loadComponent: () =>
          import('./pages/admin/escalas/escalas.component')
            .then(m => m.EscalasComponent),
        title: 'Painel de Escalas — EcoChatBotMarcx'
      },
      {
        path: 'relatorio',
        loadComponent: () =>
          import('./pages/admin/relatorio/relatorio.component')
            .then(m => m.RelatorioComponent),
        title: 'Relatório — EcoChatBotMarcx'
      }
    ]
  },

  // CHAT — Interface pública
  {
    path: 'chat',
    children: [
      {
        path: 'menu',
        loadComponent: () =>
          import('./pages/chat/hub-menu/hub-menu.component')
            .then(m => m.HubMenuComponent),
        title: 'Atendimento — EcoChatBotMarcx'
      },
      {
        path: ':canal',
        loadComponent: () =>
          import('./pages/chat/atendimento/atendimento.component')
            .then(m => m.AtendimentoComponent)
      }
    ]
  },

  // WILDCARD — Catch-all
  { path: '**', redirectTo: 'admin/dashboard' }
];

Rotas da Aplicação
Rota	Acesso	Descrição
/	Público	Redireciona para /admin/dashboard
/login	Público	Página de login
/admin/dashboard	Autenticado	Painel principal (dashboard)
/admin/atendimentos	Autenticado	Gestão de atendimentos
/admin/usuarios	Autenticado	CRUD de usuários
/admin/departamentos	Autenticado	CRUD de departamentos
/admin/canais	Autenticado	CRUD de canais de atendimento
/admin/conexoes	Autenticado	Configuração de conexões
/admin/contatos	Autenticado	Gestão de contatos
/admin/email	Autenticado	Gestão de e-mail
/admin/campanhas	Autenticado	Gestão de campanhas
/admin/arquivos	Autenticado	Gestão de arquivos
/admin/mensagens	Autenticado	Histórico de mensagens
/admin/niveis	Autenticado	Níveis de usuário
/admin/escalas	Autenticado	Painel de escalas
/admin/relatorio	Autenticado	Relatórios e análises
/chat/menu	Público	Menu de atendimento do cliente
/chat/:canal	Público	Atendimento por canal específico
Conceitos Angular Utilizados
Conceito	Sintaxe	Descrição
Routes	const routes: Routes	Array de objetos que definem a navegação
loadComponent	loadComponent: () => import(...)	Carrega componente sob demanda
canActivate	canActivate: [authGuard]	Guarda de rota para verificar autenticação
children	children: [...]	Rotas filhas aninhadas
Parâmetro de Rota	path: ':canal'	Captura valor dinâmico da URL
Wildcard	path: '**'	Captura qualquer URL não mapeada
title	title: '...'	Define o título da aba do navegador

Fluxo de Autenticação
Usuário acessa /admin/dashboard
         │
         ▼
    authGuard é executado
         │
    ┌────┴────┐
    │         │
 autenticado?  não → redireciona para /login
    │
    sim
    │
    ▼
Componente é renderizado

Parâmetros de Rota (:canal)

Exemplo de URLs:
URL	Parâmetro canal
/chat/portaria	portaria
/chat/agendamento	agendamento
/chat/financeiro	financeiro

Como acessar no componente:
import { ActivatedRoute } from '@angular/router';

constructor(private route: ActivatedRoute) {
  this.route.params.subscribe(params => {
    const canal = params['canal']; // "portaria", "agendamento", etc.
  });
}
Guia de Instalação e Uso
Pré-requisitos
Ferramenta	Versão	Observação
Node.js	18+	Runtime JavaScript
npm	9+	Gerenciador de pacotes
Angular CLI	17+	npm install -g @angular/cli
Git	-	Controle de versão
Passos para Executar

1. Instalar dependências
cd Frontend
npm install

2. Executar o servidor de desenvolvimento
ng serve

3. Acessar no navegador
http://localhost:4200

4. Build para produção
ng build --prod

Comandos Úteis
Comando	Descrição
ng serve	Executa em modo desenvolvimento
ng serve --open	Executa e abre no navegador
ng build	Gera artefatos para produção
ng test	Executa testes unitários
ng lint	Verifica qualidade do código
ng generate component nome	Gera novo componente
Solução de Problemas
Problema 1: Conflito de Rotas

Sintoma: A aplicação redireciona para a tela errada ou exibe erro 404.

Causa: Coexistência de app-routing.module.ts (NgModule) e app.routes.ts (standalone).

Solução:

    Escolha um padrão: standalone (recomendado) ou NgModule

    Se optar por standalone, remova AppModule e AppRoutingModule

    No main.ts, use:
    import { bootstrapApplication } from '@angular/platform-browser';
import { provideRouter } from '@angular/router';
import { AppComponent } from './app/app.component';
import { routes } from './app/app.routes';

bootstrapApplication(AppComponent, {
  providers: [provideRouter(routes)]
});

Problema 2: Estilos Não Funcionam

Sintoma: Os estilos CSS não são aplicados corretamente.

Causa: O arquivo variables.scss pode não ter sido encontrado.

Solução:

    Verifique se o arquivo existe em Frontend/src/assets/styles/variables.scss

    Ajuste o caminho no @import se necessário

Problema 3: Erro de Autenticação

Sintoma: O usuário é redirecionado para /login constantemente.

Causa: O authGuard não está encontrando o token de autenticação.

Solução:

    Verifique se o serviço de autenticação está funcionando

    Verifique se o token está sendo armazenado corretamente (localStorage/sessionStorage)

    Verifique a implementação do authGuard

Problema 4: Lazy Loading Não Funciona

Sintoma: O módulo não carrega quando a rota é acessada.

Causa: Problema na importação dinâmica.

Solução:

    Verifique se o caminho do import() está correto

    Verifique se o módulo exporta a constante correta

    Verifique se o componente está registrado no módulo

