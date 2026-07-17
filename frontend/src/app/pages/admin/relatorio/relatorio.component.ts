import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { AtendimentoService } from '../../../core/services/atendimento.service';
import { DepartamentoService } from '../../../core/services/departamento.service';
import { UsuarioService } from '../../../core/services/usuario.service';
import { Atendimento } from '../../../core/models/atendimento.model';
import { Departamento } from '../../../core/models/departamento.model';
import { Usuario } from '../../../core/models/usuario.model';
import { trackById } from '../../../core/utils/track-by';

function paraISO(data: Date): string {
  return data.toISOString().slice(0, 10);
}

@Component({
  selector: 'app-relatorio',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './relatorio.component.html',
  styleUrls: ['./relatorio.component.css'],
})
export class RelatorioComponent implements OnInit {
  readonly trackById = trackById;

  departamentos: Departamento[] = [];
  atendentes: Usuario[] = [];
  registros: Atendimento[] = [];
  total = 0;
  carregando = false;
  erro = '';
  atalhoAtivo = '';

  dataInicial = '';
  dataFinal = '';
  departamentoId: number | null = null;
  atendenteUsuarioId: number | null = null;

  constructor(
    private atendimentoService: AtendimentoService,
    private departamentoService: DepartamentoService,
    private usuarioService: UsuarioService,
  ) {}

  ngOnInit(): void {
    this.departamentoService.listar().subscribe(d => this.departamentos = d);
    this.usuarioService.listar({ nivel: 'atendente' }).subscribe(u => this.atendentes = u);
    this.buscar();
  }

  buscar(): void {
    this.carregando = true;
    this.erro = '';
    this.atendimentoService.listar({
      departamentoId: this.departamentoId ?? undefined,
      atendenteUsuarioId: this.atendenteUsuarioId ?? undefined,
      dataCriacaoInicio: this.dataInicial || undefined,
      dataCriacaoFim: this.dataFinal || undefined,
      limit: 50,
    }).subscribe({
      next: ({ total, registros }) => {
        this.total = total;
        this.registros = registros;
        this.carregando = false;
      },
      error: () => {
        this.carregando = false;
        this.erro = 'Não foi possível carregar os atendimentos agora.';
      },
    });
  }

  private aplicarAtalho(nome: string, ini: Date, fim: Date): void {
    this.atalhoAtivo = nome;
    this.dataInicial = paraISO(ini);
    this.dataFinal = paraISO(fim);
    this.buscar();
  }

  hoje(): void {
    const hoje = new Date();
    this.aplicarAtalho('hoje', hoje, hoje);
  }

  estaSemana(): void {
    const hoje = new Date();
    const inicio = new Date(hoje);
    inicio.setDate(hoje.getDate() - hoje.getDay());
    this.aplicarAtalho('semana', inicio, hoje);
  }

  esteMes(): void {
    const hoje = new Date();
    const inicio = new Date(hoje.getFullYear(), hoje.getMonth(), 1);
    this.aplicarAtalho('mes', inicio, hoje);
  }

  ultimos7Dias(): void {
    const hoje = new Date();
    const inicio = new Date(hoje);
    inicio.setDate(hoje.getDate() - 6);
    this.aplicarAtalho('7dias', inicio, hoje);
  }

  ultimos30Dias(): void {
    const hoje = new Date();
    const inicio = new Date(hoje);
    inicio.setDate(hoje.getDate() - 29);
    this.aplicarAtalho('30dias', inicio, hoje);
  }

  onFiltroManual(): void {
    this.atalhoAtivo = '';
    this.buscar();
  }

  nomeDepartamento(id?: number): string {
    return this.departamentos.find(d => d.id === id)?.nome ?? '—';
  }

  nomeAtendente(id?: number): string {
    return this.atendentes.find(a => a.id === id)?.nome ?? '—';
  }

  statusLabel(status: string): string {
    const rotulos: Record<string, string> = {
      aberto: 'Aberto', fila: 'Na fila', em_atendimento: 'Em atendimento', finalizado: 'Finalizado',
    };
    return rotulos[status] ?? status;
  }
}
