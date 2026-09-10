//╔══════════════════════════════════════════════════════════════════════════════╗
// ║  PROJETO.......: EcoChatBotMarcx — Sistema de Atendimento Digital          ║
// ║  ARQUIVO.......: app.component.ts                                          ║
// ║  LOCALIZAÇÃO...: Frontend/App/app.component.ts                             ║
// ║  AUTOR.........: Ademir Queiroz                                            ║
// ║  DATA..........: 08/09/2026                                                ║
// ║  VERSÃO........: 1.0.0                                                     ║
// ║                                                                            ║
// ║  DESCRIÇÃO                                                                 ║
// ║  Componente raiz da aplicação Angular. É o ponto de entrada visual e       ║
// ║  lógico do sistema, responsável por:                                       ║
// ║    • Declarar o seletor <app-root> usado em index.html                     ║
// ║    • Importar os componentes/diretivas necessários                         ║
// ║    • Associar o template HTML e os estilos SCSS                            ║
// ║    • Expor métodos e propriedades ao template                              ║
// ║                                                                            ║
// ║  CICLO DE VIDA                                                             ║
// ║  O AppComponent é instanciado UMA VEZ na inicialização da aplicação e      ║
// ║  permanece ativo durante toda a sessão do usuário.                         ║
// ╚══════════════════════════════════════════════════════════════════════════════╝


// ─────────────────────────────────────────────────────────────────────────────
// IMPORTAÇÕES
// ─────────────────────────────────────────────────────────────────────────────
// Cada import traz funcionalidades específicas do framework Angular:
//
//   @angular/core     → núcleo do framework (decorators, ciclo de vida, DI)
//   @angular/common   → diretivas comuns (*ngIf, *ngFor, pipes)
//   @angular/router   → navegação entre telas (rotas)
// ─────────────────────────────────────────────────────────────────────────────

import { Component } from '@angular/core';
//   Component → decorator que transforma uma classe TypeScript em componente
//   Angular. Um decorator é uma função especial (sintaxe @Nome) que adiciona
//   metadados à classe, informando ao Angular como ela deve ser tratada.

import { CommonModule } from '@angular/common';
//   CommonModule → módulo que contém diretivas estruturais básicas:
//     *ngIf     → renderização condicional (mostra/oculta elemento)
//     *ngFor    → repetição de elementos (loop em listas)
//     *ngSwitch → múltiplas condições
//     pipes     → transformação de dados (data, moeda, maiúsculas)

import { RouterOutlet } from '@angular/router';
//   RouterOutlet → diretiva que marca o ponto de injeção do componente ativo.
//   No template, é usada como <router-outlet></router-outlet>.

import { SidebarComponent } from './shared/components/sidebar/sidebar.component';
//   SidebarComponent → componente personalizado da barra lateral.
//   Importado para ser declarado no array "imports" do @Component.


// ─────────────────────────────────────────────────────────────────────────────
// DECORATOR @Component
// ─────────────────────────────────────────────────────────────────────────────
// O @Component é um DECORATOR — uma função que recebe um objeto de configuração
// (chamado de "objeto de metadados") e o associa à classe seguinte.
//
// SINTAXE:
//   @Decorator({
//     propriedade1: valor1,
//     propriedade2: valor2
//   })
//   export class NomeDaClasse { }
//
// PROPRIEDADES UTILIZADAS:
//   selector     → tag HTML customizada que representa este componente
//   standalone   → modo moderno (Angular 14+) que dispensa NgModule
//   imports      → lista de módulos/componentes/diretivas usados no template
//   templateUrl  → caminho do arquivo HTML associado
//   styleUrls    → array de arquivos CSS/SCSS associados
// ─────────────────────────────────────────────────────────────────────────────
@Component({
  selector: 'app-root',
  //   selector → nome da tag HTML customizada.
  //   Por convenção Angular, usa-se prefixo "app-" para evitar colisão
  //   com tags HTML nativas (<div>, <span>, etc.).
  //   No index.html, a aplicação é iniciada com: <app-root></app-root>

  standalone: true,
  //   standalone: true → modo "standalone" (independente).
  //   Significa que este componente NÃO precisa estar declarado em um @NgModule.
  //   Ele importa diretamente as dependências que usa (via array "imports").
  //   É o padrão recomendado a partir do Angular 17.

  imports: [CommonModule, RouterOutlet, SidebarComponent],
  //   imports → lista do que este componente utiliza no template:
  //     CommonModule       → permite usar *ngIf, *ngFor, pipes
  //     RouterOutlet       → permite usar <router-outlet>
  //     SidebarComponent   → permite usar <app-sidebar>

  templateUrl: './app.component.html',
  //   templateUrl → caminho relativo do arquivo HTML do template.
  //   Alternativa: usar "template: `...`" para HTML inline (curto).

  styleUrls: ['./app.component.scss']
  //   styleUrls → array de arquivos de estilo específicos deste componente.
  //   O Angular aplica "encapsulamento de escopo" (ViewEncapsulation.Emulated):
  //   os estilos só afetam este componente, não vazam para outros.
})


// ─────────────────────────────────────────────────────────────────────────────
// CLASSE DO COMPONENTE
// ─────────────────────────────────────────────────────────────────────────────
// A classe contém:
//   • PROPRIEDADES → dados que o template pode exibir (via {{ }})
//   • MÉTODOS      → funções que o template pode chamar (via (evento))
//
// O "export" torna a classe disponível para importação em outros arquivos.
// ─────────────────────────────────────────────────────────────────────────────
export class AppComponent {

  // ─────────────────────────────────────────────────────────────────────────
  // PROPRIEDADES
  // ─────────────────────────────────────────────────────────────────────────
  // Propriedades públicas ficam disponíveis para interpolação no template:
  //   No HTML: {{ title }} → exibe o valor "EcoChat Marcx"
  //
  // A sintaxe "= 'valor'" é inicialização direta (sem constructor).
  // ─────────────────────────────────────────────────────────────────────────
  title = 'EcoChat Marcx';
  //   title → título da aplicação. Pode ser usado em:
  //     • <title>{{ title }}</title> no index.html
  //     • Exibição no cabeçalho, rodapé, etc.


  // ─────────────────────────────────────────────────────────────────────────
  // MÉTODOS
  // ─────────────────────────────────────────────────────────────────────────
  // Métodos públicos podem ser chamados pelo template via event binding:
  //   No HTML: (click)="reload()" → executa este método ao clicar
  //
  // ": void" → tipagem TypeScript indicando que o método não retorna valor.
  // ─────────────────────────────────────────────────────────────────────────
  reload(): void {
    //   window → objeto global do navegador (BOM - Browser Object Model)
    //            representa a janela/aba atual do navegador.
    //
    //   location → propriedade de window que contém informações da URL atual
    //              (href, pathname, search, hash, etc.).
    //
    //   reload() → método que recarrega a página inteira, como pressionar F5.
    //              Útil para forçar sincronização com o backend após alterações.
    //
    // ATENÇÃO: reload() recarrega TUDO (HTML, CSS, JS, estado).
    //          Para atualizar apenas dados, prefira chamadas HTTP via service.
    window.location.reload();
  }
}