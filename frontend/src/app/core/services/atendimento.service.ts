import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, map } from 'rxjs';
import { environment } from '../../../environments/environment';
import { Atendimento, FiltroAtendimento } from '../models/atendimento.model';

interface ZigResponse<T = any> {
  codigo: number;
  erro?: string | null;
  dados: T;
}

@Injectable({ providedIn: 'root' })
export class AtendimentoService {
  private api = `${environment.apiUrl}/atendimento`;

  constructor(private http: HttpClient) {}

  listar(filtro: FiltroAtendimento = {}): Observable<{ total: number; registros: Atendimento[] }> {
    let params = new HttpParams()
      .set('limit', String(filtro.limit ?? 50))
      .set('page', String(filtro.page ?? 1));
    if (filtro.departamentoId != null) params = params.set('departamento_id', filtro.departamentoId);
    if (filtro.atendenteUsuarioId != null) params = params.set('atendente_usuario_id', filtro.atendenteUsuarioId);
    if (filtro.status) params = params.set('status', filtro.status);
    if (filtro.dataCriacaoInicio) params = params.set('data_criacao_inicio', filtro.dataCriacaoInicio);
    if (filtro.dataCriacaoFim) params = params.set('data_criacao_fim', filtro.dataCriacaoFim);

    return this.http.get<ZigResponse>(`${this.api}/listar`, { params }).pipe(
      map(resp => ({
        total: resp.dados?.total ?? 0,
        registros: (resp.dados?.registros ?? []).map((r: any) => this._normalizar(r)),
      })),
    );
  }

  /** Atendente assume um atendimento da fila do seu departamento. */
  puxar(atendimentoId: number, atendenteUsuarioId: number): Observable<void> {
    return this.http.post<ZigResponse>(`${this.api}/transferir`, {
      atendimento_id: atendimentoId,
      atendente_usuario_id: atendenteUsuarioId,
    }).pipe(map(() => undefined));
  }

  encerrar(atendimentoId: number, mensagem?: string): Observable<void> {
    return this.http.post<ZigResponse>(`${this.api}/encerrar`, {
      atendimento_id: atendimentoId,
      mensagem,
    }).pipe(map(() => undefined));
  }

  private _normalizar(raw: any): Atendimento {
    return {
      id: raw.id,
      protocolo: raw.protocolo,
      telefone: raw.telefone,
      nomeContato: raw.nome_contato,
      status: raw.status,
      departamentoId: raw.departamento_id,
      canalId: raw.canal_id,
      usuarioId: raw.usuario_id,
      criadoEm: raw.criado_em,
      atualizadoEm: raw.atualizado_em,
    };
  }
}
