import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, of } from 'rxjs';
import { Canal } from '../models/canal.model';

@Injectable({
  providedIn: 'root'
})
export class CanalService {
  private readonly STORAGE_KEY = 'ecochat_canais';
  private canaisSubject = new BehaviorSubject<Canal[]>([]);
  public canais$ = this.canaisSubject.asObservable();

  constructor() {
    this.carregarCanais();
  }

  private carregarCanais(): void {
    const data = localStorage.getItem(this.STORAGE_KEY);
    let canais = data ? JSON.parse(data) : [];

    if (canais.length === 0) {
      canais = [
        { id: 1, nome: 'Atendimento-Cliente', icone: '📞', descricao: 'Central de atendimento ao cliente', arquivoMenu: '1atendimento-marcx.html', ativo: true, status: 'ativo' },
        { id: 2, nome: 'Agendamento-Ambulatorial', icone: '📅', descricao: 'Agendamento de consultas ambulatoriais', arquivoMenu: '2agendamento-marcx.html', ativo: true, status: 'ativo' },
        { id: 3, nome: 'Exames-Diagnostico', icone: '🩺', descricao: 'Informações sobre exames diagnósticos', arquivoMenu: '3examesdiagnostico-marcx.html', ativo: true, status: 'ativo' },
        { id: 4, nome: 'Portaria', icone: '🚪', descricao: 'Atendimento de portaria e controle', arquivoMenu: '7portaria-marcx.html', ativo: true, status: 'ativo' },
        { id: 5, nome: 'Ouvidoria', icone: '📢', descricao: 'Canal de ouvidoria e sugestões', arquivoMenu: '8ouvidoria-marcx.html', ativo: true, status: 'ativo' },
      ];
      this.salvarCanais(canais);
    } else {
      this.canaisSubject.next(this.normalizarLista(canais));
    }
  }

  private salvarCanais(canais: Canal[]): void {
    const normalizados = this.normalizarLista(canais);
    localStorage.setItem(this.STORAGE_KEY, JSON.stringify(normalizados));
    this.canaisSubject.next(normalizados);
  }

  private normalizarLista(canais: Canal[]): Canal[] {
    return canais.map(c => ({
      ...c,
      ativo: c.ativo ?? c.status === 'ativo',
      status: c.status ?? (c.ativo ? 'ativo' : 'inativo')
    }));
  }

  listar(): Observable<Canal[]> {
    return this.canais$;
  }

  getCanais(): Canal[] {
    return this.canaisSubject.value;
  }

  getCanaisAtivos(): Canal[] {
    return this.canaisSubject.value.filter(c => (c.ativo ?? c.status === 'ativo'));
  }

  criar(canal: Partial<Canal>): Observable<Canal> {
    const novo = {
      ...canal,
      id: Date.now(),
      ativo: canal.ativo ?? true,
      status: canal.status ?? (canal.ativo ? 'ativo' : 'inativo'),
      arquivoMenu: canal.arquivoMenu ?? canal.arquivo_menu ?? ''
    } as Canal;
    this.salvarCanais([...this.canaisSubject.value, novo]);
    return of(novo);
  }

  atualizar(id: number, canal: Partial<Canal>): Observable<Canal> {
    const atual = this.canaisSubject.value.map(c => c.id === id ? { ...c, ...canal, ativo: canal.ativo ?? c.ativo ?? true, status: canal.status ?? (canal.ativo ?? c.ativo ? 'ativo' : 'inativo') } : c);
    this.salvarCanais(atual);
    const item = atual.find(c => c.id === id);
    return of(item as Canal);
  }

  deletar(id: number): Observable<void> {
    const atual = this.canaisSubject.value.filter(c => c.id !== id);
    this.salvarCanais(atual);
    return of(void 0);
  }

  adicionarCanal(canal: Omit<Canal, 'id'>): Canal {
    const novo = { ...canal, id: Date.now() } as Canal;
    this.salvarCanais([...this.canaisSubject.value, novo]);
    return novo;
  }

  deletarCanal(id: number): boolean {
    const canais = this.canaisSubject.value.filter(c => c.id !== id);
    if (canais.length === this.canaisSubject.value.length) return false;
    this.salvarCanais(canais);
    return true;
  }
}