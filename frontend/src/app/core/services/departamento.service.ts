import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Departamento } from '../models/departamento.model';
import { environment } from '../../../environments/environment';

@Injectable({ providedIn: 'root' })
export class DepartamentoService {
  private api = `${environment.apiUrl}/departamentos`;

  constructor(private http: HttpClient) {}

  listar(): Observable<Departamento[]> {
    return this.http.get<Departamento[]>(this.api);
  }

  buscarPorId(id: number): Observable<Departamento> {
    return this.http.get<Departamento>(`${this.api}/${id}`);
  }

  criar(dto: Partial<Departamento>): Observable<Departamento> {
    return this.http.post<Departamento>(this.api, dto);
  }

  atualizar(id: number, dto: Partial<Departamento>): Observable<Departamento> {
    return this.http.put<Departamento>(`${this.api}/${id}`, dto);
  }

  deletar(id: number): Observable<void> {
    return this.http.delete<void>(`${this.api}/${id}`);
  }
}
