import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Campanha, CampanhaCreateDTO } from '../../../core/models/campanha.model';
import { Contato } from '../../../core/models/contato.model';
import { Conexao } from '../../../core/models/conexao.model';
import { CampanhaService } from '../../../core/services/campanha.service';
import { ContatoService } from '../../../core/services/contato.service';
import { ConexaoService } from '../../../core/services/conexao.service';
import { trackById } from '../../../core/utils/track-by';

@Component({
  selector: 'app-campanhas',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './campanhas.component.html',
  styleUrls: ['./campanhas.component.css']
})
export class CampanhasComponent implements OnInit {

  readonly trackById = trackById;

  campanhas: Campanha[] = [];
  contatos: Contato[] = [];
  conexoes: Conexao[] = [];

  modalAberto = false;
  form: { nome: string; mensagem: string; conexaoId: number | null; contatoIds: number[] } =
    { nome: '', mensagem: '', conexaoId: null, contatoIds: [] };

  disparando: number | null = null;
  alerta: { tipo: 'sucesso' | 'erro'; msg: string } | null = null;

  constructor(
    private campanhaService: CampanhaService,
    private contatoService: ContatoService,
    private conexaoService: ConexaoService,
  ) {}

  ngOnInit(): void {
    this.carregar();
    this.contatoService.listar().subscribe(c => this.contatos = c.filter(x => x.ativo));
    this.conexaoService.listar().subscribe(c => this.conexoes = c.filter(x => x.ativo));
  }

  carregar(): void {
    this.campanhaService.listar().subscribe(c => this.campanhas = c);
  }

  abrirNovo(): void {
    this.form = { nome: '', mensagem: '', conexaoId: this.conexoes[0]?.id ?? null, contatoIds: [] };
    this.modalAberto = true;
  }

  fecharModal(): void {
    this.modalAberto = false;
  }

  toggleContato(id: number): void {
    const i = this.form.contatoIds.indexOf(id);
    if (i === -1) this.form.contatoIds.push(id); else this.form.contatoIds.splice(i, 1);
  }

  salvar(): void {
    if (!this.form.nome.trim() || !this.form.mensagem.trim() || !this.form.conexaoId) {
      this.mostrarAlerta('erro', 'Informe nome, mensagem e a conexão de envio.');
      return;
    }
    if (this.form.contatoIds.length === 0) {
      this.mostrarAlerta('erro', 'Selecione ao menos um contato.');
      return;
    }

    const dto: CampanhaCreateDTO = {
      nome: this.form.nome,
      mensagem: this.form.mensagem,
      conexaoId: this.form.conexaoId,
      contatoIds: this.form.contatoIds,
    };

    this.campanhaService.criar(dto).subscribe({
      next: () => { this.mostrarAlerta('sucesso', 'Campanha criada em rascunho.'); this.fecharModal(); this.carregar(); },
      error: () => this.mostrarAlerta('erro', 'Erro ao criar a campanha.')
    });
  }

  disparar(c: Campanha): void {
    if (!confirm(`Disparar a campanha "${c.nome}" para ${c.totalContatos} contato(s)?`)) return;
    this.disparando = c.id;
    this.campanhaService.disparar(c.id).subscribe({
      next: () => { this.disparando = null; this.mostrarAlerta('sucesso', 'Campanha disparada.'); this.carregar(); },
      error: () => { this.disparando = null; this.mostrarAlerta('erro', 'Erro ao disparar a campanha.'); }
    });
  }

  deletar(id: number): void {
    if (!confirm('Remover esta campanha?')) return;
    this.campanhaService.deletar(id).subscribe({
      next: () => { this.mostrarAlerta('sucesso', 'Campanha removida.'); this.carregar(); },
      error: () => this.mostrarAlerta('erro', 'Erro ao remover a campanha.')
    });
  }

  nomeConexao(id: number): string {
    return this.conexoes.find(c => c.id === id)?.nome ?? `#${id}`;
  }

  private mostrarAlerta(tipo: 'sucesso' | 'erro', msg: string): void {
    this.alerta = { tipo, msg };
    setTimeout(() => this.alerta = null, 4000);
  }
}
