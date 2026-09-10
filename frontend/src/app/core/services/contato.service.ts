import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, map } from 'rxjs';
import { Contato } from '../models/contato.model';
import { environment } from '../../../environments/environment';

@Injectable({ providedIn: 'root' })
export class ContatoService {
  private api = `${environment.apiUrl}/contatos`;

  constructor(private http: HttpClient) { }

  listar(): Observable<Contato[]> {
    return this.http.get<any[]>(this.api).pipe(map(cs => cs.map(c => this._normalizar(c))));
  }

  criar(dto: Partial<Contato>): Observable<Contato> {
    return this.http.post<any>(this.api, this._serializar(dto)).pipe(map(c => this._normalizar(c)));
  }

  atualizar(id: number, dto: Partial<Contato>): Observable<Contato> {
    return this.http.put<any>(`${this.api}/${id}`, this._serializar(dto)).pipe(map(c => this._normalizar(c)));
  }

  deletar(id: number): Observable<void> {
    return this.http.delete<void>(`${this.api}/${id}`);
  }

  private _normalizar(raw: any): Contato {
    return {
      id: raw.id,
      nome: raw.nome,
      telefone: raw.telefone,
      email: raw.email,
      empresa: raw.empresa,
      observacao: raw.observacao,
      origem: raw.origem,
      ativo: raw.ativo,
      criadoEm: raw.criado_em ?? raw.criadoEm,
    };
  }

  private _serializar(dto: Partial<Contato>): Record<string, unknown> {
    const { id, origem, criadoEm, ...rest } = dto as any;
    return rest;
  }
}
