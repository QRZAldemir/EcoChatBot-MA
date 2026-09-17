// src/app/features/memorandos/memorando.service.ts
import { Injectable, signal, computed, effect } from '@angular/core';

export interface Memorando {
  id: number;
  titulo: string;
  conteudo: string;
  cor: 'yellow' | 'blue' | 'green' | 'red' | 'purple';
  criadoEm: string;
}

@Injectable({ providedIn: 'root' })
export class MemorandoService {
  // 1. Estado reativo (Signal)
  private memorandosSignal = signal<Memorando[]>(this.carregarDoStorage());

  // 2. Estado derivado (Computed) - Atualiza automaticamente quando o signal muda
  // Substitui a função manual de filtrar no DOM
  memorandosFiltrados = computed(() => {
    const termo = this.termoBusca().toLowerCase();
    if (!termo) return this.memorandosSignal();
    
    return this.memorandosSignal().filter(m => 
      m.titulo.toLowerCase().includes(termo) || 
      m.conteudo.toLowerCase().includes(termo)
    );
  });

  termoBusca = signal('');

  constructor() {
    // 3. Efeito colateral: Salva no localStorage sempre que a lista muda
    effect(() => {
      localStorage.setItem('memorandos_data', JSON.stringify(this.memorandosSignal()));
    });
  }

  adicionar(memo: Omit<Memorando, 'id' | 'criadoEm'>) {
    const novo: Memorando = {
      ...memo,
      id: Date.now(),
      criadoEm: new Date().toLocaleString('pt-BR')
    };
    this.memorandosSignal.update(lista => [novo, ...lista]);
  }

  remover(id: number) {
    this.memorandosSignal.update(lista => lista.filter(m => m.id !== id));
  }

  private carregarDoStorage(): Memorando[] {
    try {
      return JSON.parse(localStorage.getItem('memorandos_data') || '[]');
    } catch {
      return [];
    }
  }
}