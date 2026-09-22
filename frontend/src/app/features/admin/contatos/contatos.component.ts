import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Contato } from '../../../core/models/contato.model';
import { ContatoService } from '../../../core/services/contato.service';
import { trackById } from '../../../core/utils/track-by';

@Component({
  selector: 'app-contatos',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './contatos.component.html',
  styleUrls: ['./contatos.component.css']
})
export class ContatosComponent implements OnInit {

  readonly trackById = trackById;

  contatos: Contato[] = [];
  busca = '';

  modalAberto = false;
  modo: 'novo' | 'editar' = 'novo';
  form: Partial<Contato> = {};

  alerta: { tipo: 'sucesso' | 'erro'; msg: string } | null = null;

  constructor(private contatoService: ContatoService) { }

  ngOnInit(): void {
    this.carregar();
  }

  carregar(): void {
    this.contatoService.listar().subscribe(c => this.contatos = c);
  }

  get contatosFiltrados(): Contato[] {
    const termo = this.busca.trim().toLowerCase();
    if (!termo) return this.contatos;
    return this.contatos.filter(c =>
      c.nome.toLowerCase().includes(termo) || c.telefone.includes(termo)
    );
  }

  abrirNovo(): void {
    this.modo = 'novo';
    this.form = { ativo: true };
    this.modalAberto = true;
  }

  abrirEditar(c: Contato): void {
    this.modo = 'editar';
    this.form = { ...c };
    this.modalAberto = true;
  }

  fecharModal(): void {
    this.modalAberto = false;
  }

  salvar(): void {
    if (!this.form.nome?.trim() || !this.form.telefone?.trim()) {
      this.mostrarAlerta('erro', 'Informe nome e telefone do contato.');
      return;
    }

    if (this.modo === 'editar' && this.form.id) {
      this.contatoService.atualizar(this.form.id, this.form).subscribe({
        next: () => { this.mostrarAlerta('sucesso', 'Contato atualizado.'); this.fecharModal(); this.carregar(); },
        error: () => this.mostrarAlerta('erro', 'Erro ao salvar o contato.')
      });
      return;
    }

    this.contatoService.criar(this.form).subscribe({
      next: () => { this.mostrarAlerta('sucesso', 'Contato cadastrado.'); this.fecharModal(); this.carregar(); },
      error: () => this.mostrarAlerta('erro', 'Erro ao cadastrar o contato.')
    });
  }

  deletar(id: number): void {
    if (!confirm('Remover este contato?')) return;
    this.contatoService.deletar(id).subscribe({
      next: () => { this.mostrarAlerta('sucesso', 'Contato removido.'); this.carregar(); },
      error: () => this.mostrarAlerta('erro', 'Erro ao remover o contato.')
    });
  }

  private mostrarAlerta(tipo: 'sucesso' | 'erro', msg: string): void {
    this.alerta = { tipo, msg };
    setTimeout(() => this.alerta = null, 4000);
  }
}
