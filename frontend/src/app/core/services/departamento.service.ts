import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable, map, of } from 'rxjs';
import { Departamento } from '../models/departamento.model';
import { environment } from '../../../environments/environment';

@Injectable({ providedIn: 'root' })
export class DepartamentoService {
  private readonly STORAGE_KEY = 'ecochat_departamentos';
  private departamentosSubject = new BehaviorSubject<Departamento[]>([]);
  public departamentos$ = this.departamentosSubject.asObservable();

  private api = `${environment.apiUrl}/departamentos`;

  constructor(private http: HttpClient) {
    this.carregarDepartamentos();
  }

  private carregarDepartamentos(): void {
    const raw = localStorage.getItem(this.STORAGE_KEY);
    const data = raw ? JSON.parse(raw) : [
      { id: 1, nome: 'Atendimento', status: 'ativo' },
      { id: 2, nome: 'Comercial', status: 'ativo' },
      { id: 3, nome: 'Suporte', status: 'ativo' },
      { id: 4, nome: 'Operações', status: 'ativo' },
    ];
    this.departamentosSubject.next(data);
    localStorage.setItem(this.STORAGE_KEY, JSON.stringify(data));
  }

  private salvarDepartamentos(departamentos: Departamento[]): void {
    localStorage.setItem(this.STORAGE_KEY, JSON.stringify(departamentos));
    this.departamentosSubject.next(departamentos);
  }

  listar(): Observable<Departamento[]> {
    return this.departamentos$.pipe(map(ds => ds.map(d => this._normalizar(d))));
  }

  buscarPorId(id: number): Observable<Departamento> {
    const item = this.departamentosSubject.value.find(d => d.id === id);
    return of(item ? this._normalizar(item) : { id, nome: '', status: 'ativo' });
  }

  criar(dto: Partial<Departamento>): Observable<Departamento> {
    const novo: Departamento = {
      id: Date.now(),
      nome: dto.nome ?? 'Novo departamento',
      desc: dto.desc,
      status: dto.status ?? 'ativo'
    };
    const atual = [...this.departamentosSubject.value, novo];
    this.salvarDepartamentos(atual);
    return of(this._normalizar(novo));
  }

  atualizar(id: number, dto: Partial<Departamento>): Observable<Departamento> {
    const atual = this.departamentosSubject.value.map(d => d.id === id ? { ...d, ...dto } : d);
    this.salvarDepartamentos(atual);
    const item = atual.find(d => d.id === id);
    return of(item ? this._normalizar(item) : { id, nome: dto.nome ?? '', status: dto.status ?? 'ativo' });
  }

  deletar(id: number): Observable<void> {
    const atual = this.departamentosSubject.value.filter(d => d.id !== id);
    this.salvarDepartamentos(atual);
    return of(void 0);
  }

  private _normalizar(raw: any): Departamento {
    return {
      id: raw.id,
      nome: raw.nome,
      desc: raw.desc ?? raw.descricao,
      status: raw.status ?? (raw.ativo ? 'ativo' : 'inativo')
    };
  }
}
