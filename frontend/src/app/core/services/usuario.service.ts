import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, map } from 'rxjs';
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
    if (filtro?.departamentoId) params = params.set('departamento_id', filtro.departamentoId);
    if (filtro?.canalId)        params = params.set('canal_id', filtro.canalId);
    if (filtro?.nivel)          params = params.set('nivel', filtro.nivel);
    if (filtro?.status)         params = params.set('ativo', filtro.status === 'ativo' ? 'true' : 'false');
    return this.http.get<any[]>(this.api, { params }).pipe(map(us => us.map(u => this._normalizar(u))));
  }

  buscarPorId(id: number): Observable<Usuario> {
    return this.http.get<any>(`${this.api}/${id}`).pipe(map(u => this._normalizar(u)));
  }

  criar(dto: Partial<Usuario>): Observable<Usuario> {
    return this.http.post<any>(this.api, this._serializar(dto)).pipe(map(u => this._normalizar(u)));
  }

  atualizar(id: number, dto: Partial<Usuario>): Observable<Usuario> {
    return this.http.put<any>(`${this.api}/${id}`, this._serializar(dto)).pipe(map(u => this._normalizar(u)));
  }

  deletar(id: number): Observable<void> {
    return this.http.delete<void>(`${this.api}/${id}`);
  }

  agruparPorDepartamento(usuarios: Usuario[]): Map<string, Usuario[]> {
    return usuarios.reduce((mapa, u) => {
      const depto = u.departamentoNome ?? 'Sem Departamento';
      if (!mapa.has(depto)) mapa.set(depto, []);
      mapa.get(depto)!.push(u);
      return mapa;
    }, new Map<string, Usuario[]>());
  }

  private _normalizar(raw: any): Usuario {
    return {
      ...raw,
      departamentoId: raw.departamento_id ?? raw.departamentoId,
      departamentoNome: raw.departamento?.nome ?? raw.departamentoNome,
      canalId: raw.canal_id ?? raw.canalId,
      canalNome: raw.canal?.nome ?? raw.canalNome,
      canalArquivo: raw.canal?.arquivo_menu ?? raw.canalArquivo,
      nivel: raw.nivel ?? 'atendente',
      ativo: raw.ativo ?? true,
      status: (raw.ativo !== false) ? 'ativo' : 'inativo',
      criado_em: raw.criado_em,
    } as Usuario;
  }

  private _serializar(dto: Partial<Usuario>): Record<string, unknown> {
    const { departamentoId, canalId, status, ...rest } = dto as any;
    return {
      ...rest,
      ...(departamentoId !== undefined && { departamento_id: departamentoId }),
      ...(canalId !== undefined         && { canal_id: canalId }),
      ...(status !== undefined          && { ativo: status === 'ativo' }),
    };
  }
}
