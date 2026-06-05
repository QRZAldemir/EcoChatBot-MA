import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Usuario } from '../models/usuario.model';
import { environment } from '../../../environments/environment';

export interface FiltroUsuario {
  nome?: string;
  departamentoId?: number;
  canalId?: number;
  nivel?: string;
  status?: string;
}

@Injectable({ providedIn: 'root' })
export class UsuarioService {
  private api = `${environment.apiUrl}/usuarios`;

  constructor(private http: HttpClient) {}

  listar(filtro?: FiltroUsuario): Observable<Usuario[]> {
    let params = new HttpParams();
    if (filtro?.nome)           params = params.set('nome', filtro.nome);
    if (filtro?.departamentoId) params = params.set('departamentoId', filtro.departamentoId);
    if (filtro?.canalId)        params = params.set('canalId', filtro.canalId);
    if (filtro?.nivel)          params = params.set('nivel', filtro.nivel);
    if (filtro?.status)         params = params.set('status', filtro.status);
    return this.http.get<Usuario[]>(this.api, { params });
  }

  buscarPorId(id: number): Observable<Usuario> {
    return this.http.get<Usuario>(`${this.api}/${id}`);
  }

  criar(dto: Partial<Usuario>): Observable<Usuario> {
    return this.http.post<Usuario>(this.api, dto);
  }

  atualizar(id: number, dto: Partial<Usuario>): Observable<Usuario> {
    return this.http.put<Usuario>(`${this.api}/${id}`, dto);
  }

  deletar(id: number): Observable<void> {
    return this.http.delete<void>(`${this.api}/${id}`);
  }

  // Agrupa usuários por departamento (útil para exibição na tabela)
  agruparPorDepartamento(usuarios: Usuario[]): Map<string, Usuario[]> {
    return usuarios.reduce((mapa, u) => {
      const depto = u.departamentoNome ?? 'Sem Departamento';
      if (!mapa.has(depto)) mapa.set(depto, []);
      mapa.get(depto)!.push(u);
      return mapa;
    }, new Map<string, Usuario[]>());
  }
}
