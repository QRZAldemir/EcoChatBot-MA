import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, map } from 'rxjs';
import { Departamento } from '../models/departamento.model';
import { environment } from '../../../environments/environment';

@Injectable({ providedIn: 'root' })
export class DepartamentoService {
  private api = `${environment.apiUrl}/departamentos`;

  constructor(private http: HttpClient) {}

  listar(): Observable<Departamento[]> {
    return this.http.get<any[]>(this.api).pipe(map(ds => ds.map(d => this._normalizar(d))));
  }

  buscarPorId(id: number): Observable<Departamento> {
    return this.http.get<any>(`${this.api}/${id}`).pipe(map(d => this._normalizar(d)));
  }

  criar(dto: Partial<Departamento>): Observable<Departamento> {
    return this.http.post<any>(this.api, dto).pipe(map(d => this._normalizar(d)));
  }

  atualizar(id: number, dto: Partial<Departamento>): Observable<Departamento> {
    return this.http.put<any>(`${this.api}/${id}`, dto).pipe(map(d => this._normalizar(d)));
  }

  deletar(id: number): Observable<void> {
    return this.http.delete<void>(`${this.api}/${id}`);
  }

  // Converte snake_case do backend (criado_em) → camelCase do model (dataCriacao),
  // igual ao padrão já usado em CanalService/UsuarioService/etc.
  private _normalizar(raw: any): Departamento {
    return {
      ...raw,
      dataCriacao: raw.criado_em ?? raw.dataCriacao,
    };
  }
}
