import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Arquivo } from '../../../core/models/arquivo.model';
import { ArquivoService } from '../../../core/services/arquivo.service';
import { trackById } from '../../../core/utils/track-by';

@Component({
  selector: 'app-arquivos',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './arquivos.component.html',
  styleUrls: ['./arquivos.component.css']
})
export class ArquivosComponent implements OnInit {

  readonly trackById = trackById;

  arquivos: Arquivo[] = [];

  modalAberto = false;
  arquivoSelecionado: File | null = null;
  descricao = '';
  enviando = false;

  alerta: { tipo: 'sucesso' | 'erro'; msg: string } | null = null;

  constructor(private arquivoService: ArquivoService) {}

  ngOnInit(): void {
    this.carregar();
  }

  carregar(): void {
    this.arquivoService.listar().subscribe(a => this.arquivos = a);
  }

  abrirNovo(): void {
    this.arquivoSelecionado = null;
    this.descricao = '';
    this.modalAberto = true;
  }

  fecharModal(): void {
    this.modalAberto = false;
  }

  aoSelecionarArquivo(evento: Event): void {
    const input = evento.target as HTMLInputElement;
    this.arquivoSelecionado = input.files?.[0] ?? null;
  }

  enviar(): void {
    if (!this.arquivoSelecionado) {
      this.mostrarAlerta('erro', 'Selecione um arquivo.');
      return;
    }

    this.enviando = true;
    this.arquivoService.enviar(this.arquivoSelecionado, this.descricao).subscribe({
      next: () => { this.enviando = false; this.mostrarAlerta('sucesso', 'Arquivo enviado.'); this.fecharModal(); this.carregar(); },
      error: () => { this.enviando = false; this.mostrarAlerta('erro', 'Erro ao enviar o arquivo.'); }
    });
  }

  baixar(a: Arquivo): void {
    window.open(this.arquivoService.downloadUrl(a.id), '_blank');
  }

  deletar(id: number): void {
    if (!confirm('Remover este arquivo?')) return;
    this.arquivoService.deletar(id).subscribe({
      next: () => { this.mostrarAlerta('sucesso', 'Arquivo removido.'); this.carregar(); },
      error: () => this.mostrarAlerta('erro', 'Erro ao remover o arquivo.')
    });
  }

  formatarTamanho(bytes?: number): string {
    if (!bytes) return '—';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }

  private mostrarAlerta(tipo: 'sucesso' | 'erro', msg: string): void {
    this.alerta = { tipo, msg };
    setTimeout(() => this.alerta = null, 4000);
  }
}
