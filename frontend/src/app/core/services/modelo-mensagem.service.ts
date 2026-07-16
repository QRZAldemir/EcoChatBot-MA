import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, map } from 'rxjs';
import { ModeloMensagem } from '../models/modelo-mensagem.model';
import { environment } from '../../../environments/environment';

@Injectable({ providedIn: 'root' })
export class ModeloMensagemService {
  private api = `${environment.apiUrl}/modelos-mensagem`;

  constructor(private http: HttpClient) {}

  listar(): Observable<ModeloMensagem[]> {
    return this.http.get<ModeloMensagem[]>(this.api).pipe(map(ms => ms.map(m => this._normalizar(m))));
  }

  buscarPorId(id: number): Observable<ModeloMensagem> {
    return this.http.get<ModeloMensagem>(`${this.api}/${id}`).pipe(map(m => this._normalizar(m)));
  }

  criar(dto: Partial<ModeloMensagem>): Observable<ModeloMensagem> {
    return this.http.post<ModeloMensagem>(this.api, this._serializar(dto)).pipe(map(m => this._normalizar(m)));
  }

  atualizar(id: number, dto: Partial<ModeloMensagem>): Observable<ModeloMensagem> {
    return this.http.put<ModeloMensagem>(`${this.api}/${id}`, this._serializar(dto)).pipe(map(m => this._normalizar(m)));
  }

  deletar(id: number): Observable<void> {
    return this.http.delete<void>(`${this.api}/${id}`);
  }

  private _normalizar(raw: any): ModeloMensagem {
    return {
      ...raw,
      departamentoId: raw.departamento_id ?? raw.departamentoId,
      departamentoNome: raw.departamento?.nome ?? raw.departamentoNome,
      criadoEm: raw.criado_em ?? raw.criadoEm,
    };
  }

  private _serializar(dto: Partial<ModeloMensagem>): Record<string, unknown> {
    const { departamentoId, departamentoNome, criadoEm, ...rest } = dto as any;
    return {
      ...rest,
      ...(departamentoId !== undefined && { departamento_id: departamentoId }),
    };
  }
}
