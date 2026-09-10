import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';
import { Turno, TurnoDias, DIAS_SEMANA } from '../models/turno.model';

@Injectable({
  providedIn: 'root'
})
export class TurnoService {
  private readonly STORAGE_KEY = 'ecochat_turnos';
  private turnosSubject = new BehaviorSubject<Turno[]>([]);
  public turnos$ = this.turnosSubject.asObservable();

  constructor() {
    this.carregarTurnos();
  }

  private criarDiasPadrao(ini: string = '08:00', fim: string = '17:00'): TurnoDias {
    const dias: Partial<Record<keyof TurnoDias, { ini: string; fim: string }[]>> = {};
    DIAS_SEMANA.forEach(({ key }) => {
      dias[key] = [{ ini, fim }];
    });
    return dias as TurnoDias;
  }

  private carregarTurnos(): void {
    const data = localStorage.getItem(this.STORAGE_KEY);
    let turnos = data ? JSON.parse(data) : [];

    if (turnos.length === 0) {
      turnos = [
        { id: 1, desc: 'Manhã', dias: this.criarDiasPadrao('06:00', '14:00'), acao: 'fila', msgAndamento: '', msgEncerramento: '', status: 'ativo' },
        { id: 2, desc: 'Tarde', dias: this.criarDiasPadrao('14:00', '22:00'), acao: 'fila', msgAndamento: '', msgEncerramento: '', status: 'ativo' },
        { id: 3, desc: 'Noite', dias: this.criarDiasPadrao('22:00', '23:59'), acao: 'mensagem', msgAndamento: '', msgEncerramento: '', status: 'ativo' },
        { id: 4, desc: 'Integral', dias: this.criarDiasPadrao('00:00', '23:59'), acao: 'fila', msgAndamento: '', msgEncerramento: '', status: 'ativo' },
      ];
      this.salvarTurnos(turnos);
    } else {
      this.turnosSubject.next(turnos);
    }
  }

  private salvarTurnos(turnos: Turno[]): void {
    localStorage.setItem(this.STORAGE_KEY, JSON.stringify(turnos));
    this.turnosSubject.next(turnos);
  }

  getTurnos(): Turno[] {
    return this.turnosSubject.value;
  }

  getTurnosAtivos(): Turno[] {
    return this.turnosSubject.value.filter(t => t.status === 'ativo');
  }

  adicionarTurno(turno: Omit<Turno, 'id'>): Turno {
    const turnos = this.turnosSubject.value;
    const novo = { ...turno, id: Date.now() };
    this.salvarTurnos([...turnos, novo]);
    return novo;
  }

  deletarTurno(id: number): boolean {
    const turnos = this.turnosSubject.value.filter(t => t.id !== id);
    if (turnos.length === this.turnosSubject.value.length) return false;
    this.salvarTurnos(turnos);
    return true;
  }

  // Método para criar um novo objeto de dias vazio para formulário
  criarDiasVazios(): TurnoDias {
    const dias: Partial<Record<keyof TurnoDias, { ini: string; fim: string }[]>> = {};
    DIAS_SEMANA.forEach(({ key }) => {
      dias[key] = [];
    });
    return dias as TurnoDias;
  }

  // Método para criar um novo objeto de dias com um horário padrão
  criarDiasPadraoParaForm(ini: string = '08:00', fim: string = '17:00'): TurnoDias {
    const dias: Partial<Record<keyof TurnoDias, { ini: string; fim: string }[]>> = {};
    DIAS_SEMANA.forEach(({ key }) => {
      dias[key] = [{ ini, fim }];
    });
    return dias as TurnoDias;
  }
}