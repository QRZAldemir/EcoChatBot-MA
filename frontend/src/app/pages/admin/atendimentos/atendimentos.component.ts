import { Component, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subscription, catchError, forkJoin, interval, of, startWith, switchMap, tap } from 'rxjs';
import { AuthService } from '../../../core/services/auth.service';
import { AtendimentoService } from '../../../core/services/atendimento.service';
import { DepartamentoService } from '../../../core/services/departamento.service';
import { Atendimento } from '../../../core/models/atendimento.model';
import { UsuarioLogado } from '../../../core/models/auth.model';
import { trackById } from '../../../core/utils/track-by';

// Polling simples: suficiente para um painel de atendimento/recepção e
// muito mais barato de manter que websocket (ver decisão registrada com o
// usuário — real-time via polling é o padrão adotado neste projeto).
const POLL_MS = 8000;

@Component({
  selector: 'app-atendimentos',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './atendimentos.component.html',
  styleUrls: ['./atendimentos.component.css'],
})
export class AtendimentosComponent implements OnInit, OnDestroy {
  readonly trackById = trackById;

  usuario: UsuarioLogado | null = this.auth.getUsuarioAtual();
  departamentoNome = '';
  fila: Atendimento[] = [];
  meus: Atendimento[] = [];
  carregando = true;
  erro = '';

  private pollSub?: Subscription;

  constructor(
    private auth: AuthService,
    private atendimentoService: AtendimentoService,
    private departamentoService: DepartamentoService,
  ) {}

  ngOnInit(): void {
    if (!this.usuario?.departamentoId) {
      this.carregando = false;
      return;
    }

    this.departamentoService.buscarPorId(this.usuario.departamentoId).subscribe({
      next: d => this.departamentoNome = d.nome,
      error: () => {},
    });

    this.pollSub = interval(POLL_MS).pipe(
      startWith(0),
      switchMap(() => this.carregar()),
    ).subscribe();
  }

  ngOnDestroy(): void {
    this.pollSub?.unsubscribe();
  }

  puxar(a: Atendimento): void {
    if (!this.usuario) return;
    this.atendimentoService.puxar(a.id, this.usuario.id).subscribe({
      next: () => this.carregar().subscribe(),
      error: () => this.erro = `Não foi possível puxar o atendimento ${a.protocolo}.`,
    });
  }

  encerrar(a: Atendimento): void {
    if (!confirm(`Encerrar o atendimento ${a.protocolo}?`)) return;
    this.atendimentoService.encerrar(a.id).subscribe({
      next: () => this.carregar().subscribe(),
      error: () => this.erro = `Não foi possível encerrar o atendimento ${a.protocolo}.`,
    });
  }

  tempoDecorrido(dataIso?: string): string {
    if (!dataIso) return '—';
    const minutos = Math.floor((Date.now() - new Date(dataIso).getTime()) / 60000);
    if (minutos < 1) return 'agora';
    if (minutos < 60) return `${minutos}m`;
    const horas = Math.floor(minutos / 60);
    if (horas < 24) return `${horas}h${minutos % 60}m`;
    return `${Math.floor(horas / 24)}d`;
  }

  private carregar() {
    const usuario = this.usuario!;
    return forkJoin({
      fila: this.atendimentoService.listar({ departamentoId: usuario.departamentoId, status: 'fila' }),
      meus: this.atendimentoService.listar({ atendenteUsuarioId: usuario.id, status: 'em_atendimento' }),
    }).pipe(
      tap(({ fila, meus }) => {
        this.fila = fila.registros;
        this.meus = meus.registros;
        this.carregando = false;
        this.erro = '';
      }),
      catchError(() => {
        this.carregando = false;
        this.erro = 'Não foi possível atualizar os atendimentos agora.';
        return of(null);
      }),
    );
  }
}
