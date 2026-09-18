/**
 * ==============================================================================
 * PROJETO: EcoChatBotMarcx - Omnichannel SaaS
 * MÓDULO: mensagens.component.ts
 * AUTOR: Aldemir Queiroz
 * CONTATO: [Inserir E-mail] | [Inserir LinkedIn] | [Inserir GitHub]
 * DATA: 2024-05-20
 * ==============================================================================
 * PROPÓSITO:
 * Renderizar a interface de usuário para gerenciamento de Modelos de Mensagem.
 * Utiliza a arquitetura Standalone do Angular 17 e o sistema de reatividade 
 * baseado em Signals (signal, computed) para filtragem em tempo real, 
 * eliminando a necessidade de Zone.js e otimizando a detecção de mudanças.
 *
 * ARQUITETURA E INTEGRAÇÃO:
 * Este componente é a camada de apresentação (UI Layer) no Frontend.
 * CONEXÃO: Ele NÃO é isolado. Injeta e depende do `ModeloMensagemService` 
 * (Serviço HTTP do Angular). O `ModeloMensagemService`, por sua vez, faz 
 * chamadas HTTP (GET/POST/PUT/DELETE) para os endpoints REST do Backend 
 * (ex: `/api/mensagens`), fechando o ciclo de integração Full-Stack.
 * ==============================================================================
 */
import { Component, signal, computed, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ModeloMensagemService } from '../../core/services/modelo-mensagem.service';

@Component({
  selector: 'app-mensagens',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './mensagens.component.html',
  styleUrls: ['./mensagens.component.scss']
})
export class MensagensComponent implements OnInit {
  private service = inject(ModeloMensagemService);
  
  // Estado reativo local
  mensagens = signal<any[]>([]);
  filtro = signal<string>('');
  isLoading = signal<boolean>(false);

  // Computação reativa: filtra a lista sempre que o signal 'filtro' ou 'mensagens' muda
  mensagensFiltradas = computed(() => {
    const termo = this.filtro().toLowerCase();
    return termo 
      ? this.mensagens().filter(m => m.texto.toLowerCase().includes(termo)) 
      : this.mensagens();
  });

  async ngOnInit() {
    this.isLoading.set(true);
    try {
      const data = await this.service.listar().toPromise();
      this.mensagens.set(data || []);
    } finally {
      this.isLoading.set(false);
    }
  }
}