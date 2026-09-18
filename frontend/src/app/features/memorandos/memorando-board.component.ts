// src/app/features/memorandos/memorando-board.component.ts
import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MemorandoService } from './memorando.service';

@Component({
  selector: 'app-memorando-board',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <section class="panel" aria-labelledby="titulo-memorandos">
      <header class="panel-header">
        <h2 id="titulo-memorandos">📝 Memorandos</h2>
      </header>

      <!-- Toolbar com Acessibilidade -->
      <div class="toolbar" role="toolbar" aria-label="Ferramentas de memorandos">
        <span>Novo memorando:</span>
        
        <!-- CORREÇÃO A11Y: Botões de cor agora são <button> reais, não <div> com onclick -->
        @for (cor of coresDisponiveis; track cor) {
          <button 
            type="button"
            class="btn-cor {{cor}}"
            [attr.aria-label]="'Criar memorando na cor ' + cor"
            (click)="abrirModal(cor)">
            <span aria-hidden="true">🟡</span> <!-- Ícone decorativo, ignorado por leitores de tela -->
          </button>
        }

        <div class="search-box">
          <!-- CORREÇÃO A11Y: Label explícito vinculado ao input -->
          <label for="busca-memo" class="sr-only">Buscar memorandos por título ou conteúdo</label>
          <input 
            id="busca-memo"
            type="text" 
            [(ngModel)]="memoService.termoBusca" 
            placeholder="Localizar..."
            aria-describedby="busca-ajuda"
          >
        </div>
        <span id="busca-ajuda" class="sr-only">A lista abaixo será filtrada automaticamente enquanto você digita.</span>
      </div>

      <!-- CORREÇÃO A11Y: aria-live anuncia mudanças na lista para leitores de tela -->
      <div class="memorandos-grid" aria-live="polite">
        @if (memoService.memorandosFiltrados().length === 0) {
          <p class="empty" role="status">Nenhum memorando encontrado.</p>
        } @else {
          @for (memo of memoService.memorandosFiltrados(); track memo.id) {
            <article 
              class="memorando-card" 
              [attr.data-color]="memo.cor"
              tabindex="0" 
              role="article"
              [attr.aria-label]="'Memorando: ' + memo.titulo"
              (keydown.enter)="expandir(memo)"
              (click)="expandir(memo)">
              
              <div class="memo-header">
                <span class="memo-title">{{ memo.titulo }}</span>
                <time class="memo-date" [attr.datetime]="memo.criadoEm">{{ memo.criadoEm }}</time>
              </div>
              
              <div class="memo-body">
                <pre>{{ memo.conteudo }}</pre>
              </div>

              <div class="memo-actions">
                <!-- CORREÇÃO A11Y: aria-label descreve a ação, já que o botão só tem ícone -->
                <button class="btn-icon" (click)="copiar(memo); $event.stopPropagation()" aria-label="Copiar conteúdo do memorando">
                  📋
                </button>
                <button class="btn-icon danger" (click)="memoService.remover(memo.id); $event.stopPropagation()" aria-label="Excluir este memorando">
                  🗑️
                </button>
              </div>
            </article>
          }
        }
      </div>
    </section>
  `,
  styles: [`
    /* Estilos específicos do componente, sem ::ng-deep */
    .btn-cor { width: 32px; height: 32px; border-radius: 50%; border: 2px solid transparent; cursor: pointer; transition: transform 0.15s; }
    .btn-cor:focus-visible { outline: 2px solid var(--blue); outline-offset: 2px; }
    .btn-cor:hover { transform: scale(1.1); }
    .btn-cor.yellow { background: #f59e0b; }
    /* ... demais cores ... */
  `]
})
export class MemorandoBoardComponent {
  memoService = inject(MemorandoService);
  
  coresDisponiveis = ['yellow', 'blue', 'green', 'red', 'purple'] as const;

  abrirModal(cor: string) {
    // Lógica para abrir modal (pode ser um componente ModalService)
    console.log('Abrir modal para cor:', cor);
  }

  expandir(memo: any) {
    // Lógica de expansão
  }

  copiar(memo: any) {
    navigator.clipboard.writeText(`${memo.titulo}\n${memo.conteudo}`);
    // Ideal: usar um Toast Service para feedback visual e aria-live
  }
}