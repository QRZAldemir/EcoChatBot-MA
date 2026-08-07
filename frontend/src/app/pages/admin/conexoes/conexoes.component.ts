import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Conexao, ConexaoQRCode } from '../../../core/models/conexao.model';
import { ConexaoService } from '../../../core/services/conexao.service';
import { trackById } from '../../../core/utils/track-by';

@Component({
  selector: 'app-conexoes',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './conexoes.component.html',
  styleUrls: ['./conexoes.component.css']
})
export class ConexoesComponent implements OnInit {

  readonly trackById = trackById;

  conexoes: Conexao[] = [];
  selecionadaId: number | null = null;

  modalAberto = false;
  modo: 'novo' | 'editar' = 'novo';
  form: Partial<Conexao> = {};

  qrModalAberto = false;
  qrAtual: ConexaoQRCode | null = null;

  alerta: { tipo: 'sucesso' | 'erro'; msg: string } | null = null;

  constructor(private conexaoService: ConexaoService) {}

  ngOnInit(): void {
    this.carregar();
  }

  carregar(): void {
    this.conexaoService.listar().subscribe(c => this.conexoes = c);
  }

  get selecionada(): Conexao | undefined {
    return this.conexoes.find(c => c.id === this.selecionadaId);
  }

  selecionar(id: number): void {
    this.selecionadaId = id;
  }

  // ── Modal cadastro/edição ──────────────────────────────────────────

  abrirNovo(): void {
    this.modo = 'novo';
    this.form = { atendimento: 'automatico' };
    this.modalAberto = true;
  }

  abrirEditar(c: Conexao): void {
    this.modo = 'editar';
    this.form = { ...c };
    this.modalAberto = true;
  }

  fecharModal(): void {
    this.modalAberto = false;
  }

  salvar(): void {
    if (!this.form.nome?.trim()) {
      this.mostrarAlerta('erro', 'Informe o nome da conexão.');
      return;
    }

    if (this.modo === 'editar' && this.form.id) {
      this.conexaoService.atualizar(this.form.id, this.form).subscribe({
        next: () => { this.mostrarAlerta('sucesso', 'Conexão atualizada.'); this.fecharModal(); this.carregar(); },
        error: () => this.mostrarAlerta('erro', 'Erro ao salvar a conexão.')
      });
      return;
    }

    this.conexaoService.criar(this.form).subscribe({
      next: (r) => { this.fecharModal(); this.carregar(); this.abrirQr(r); },
      error: () => this.mostrarAlerta('erro', 'Erro ao criar a conexão.')
    });
  }

  deletar(id: number): void {
    if (!confirm('Remover esta conexão?')) return;
    this.conexaoService.deletar(id).subscribe({
      next: () => {
        if (this.selecionadaId === id) this.selecionadaId = null;
        this.mostrarAlerta('sucesso', 'Conexão removida.');
        this.carregar();
      },
      error: () => this.mostrarAlerta('erro', 'Erro ao remover a conexão.')
    });
  }

  // ── QR Code de pareamento ───────────────────────────────────────────

  private abrirQr(r: ConexaoQRCode): void {
    this.qrAtual = r;
    this.qrModalAberto = true;
  }

  fecharQr(): void {
    this.qrModalAberto = false;
    this.qrAtual = null;
  }

  // ── Ações do painel de controle (agem sobre a conexão selecionada) ──

  private exigirSelecao(): number | null {
    if (this.selecionadaId == null) {
      this.mostrarAlerta('erro', 'Selecione uma conexão na tabela.');
      return null;
    }
    return this.selecionadaId;
  }

  atualizarStatus(): void {
    const id = this.exigirSelecao();
    if (id == null) return;
    this.conexaoService.atualizarStatus(id).subscribe({
      next: () => { this.carregar(); this.mostrarAlerta('sucesso', 'Status atualizado.'); },
      error: () => this.mostrarAlerta('erro', 'Não foi possível atualizar o status.')
    });
  }

  desconectar(): void {
    const id = this.exigirSelecao();
    if (id == null) return;
    this.conexaoService.desconectar(id).subscribe({
      next: () => { this.carregar(); this.mostrarAlerta('sucesso', 'Conexão desconectada.'); },
      error: () => this.mostrarAlerta('erro', 'Erro ao desconectar.')
    });
  }

  reconectar(): void {
    const id = this.exigirSelecao();
    if (id == null) return;
    this.conexaoService.reconectar(id).subscribe({
      next: (r) => { this.carregar(); this.abrirQr(r); },
      error: () => this.mostrarAlerta('erro', 'Erro ao reconectar.')
    });
  }

  limparFila(): void {
    const id = this.exigirSelecao();
    if (id == null) return;
    this.conexaoService.limparFila(id).subscribe({
      next: () => { this.carregar(); this.mostrarAlerta('sucesso', 'Fila desta conexão foi limpa.'); },
      error: () => this.mostrarAlerta('erro', 'Erro ao limpar a fila.')
    });
  }

  tornarPadrao(): void {
    const id = this.exigirSelecao();
    if (id == null) return;
    this.conexaoService.tornarPadrao(id).subscribe({
      next: () => { this.carregar(); this.mostrarAlerta('sucesso', 'Definida como número administrativo principal.'); },
      error: () => this.mostrarAlerta('erro', 'Erro ao definir como padrão.')
    });
  }

  alternarAtivo(): void {
    const id = this.exigirSelecao();
    if (id == null) return;
    this.conexaoService.alternarAtivo(id).subscribe({
      next: (c) => { this.carregar(); this.mostrarAlerta('sucesso', c.ativo ? 'Conexão ativada.' : 'Conexão desativada.'); },
      error: () => this.mostrarAlerta('erro', 'Erro ao alternar a conexão.')
    });
  }

  private mostrarAlerta(tipo: 'sucesso' | 'erro', msg: string): void {
    this.alerta = { tipo, msg };
    setTimeout(() => this.alerta = null, 4000);
  }
}
