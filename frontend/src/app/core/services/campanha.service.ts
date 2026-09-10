import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, map } from 'rxjs';
import { Campanha, CampanhaDetalhe, CampanhaCreateDTO } from '../models/campanha.model';
import { environment } from '../../../environments/environment';

@Injectable({ providedIn: 'root' })
export class CampanhaService {
  private api = `${environment.apiUrl}/campanhas`;

  constructor(private http: HttpClient) { }

  listar(): Observable<Campanha[]> {
    return this.http.get<any[]>(this.api).pipe(map(cs => cs.map(c => this._normalizar(c))));
  }

  buscar(id: number): Observable<CampanhaDetalhe> {
    return this.http.get<any>(`${this.api}/${id}`).pipe(map(c => this._normalizarDetalhe(c)));
  }

  criar(dto: CampanhaCreateDTO): Observable<Campanha> {
    const payload = { nome: dto.nome, mensagem: dto.mensagem, conexao_id: dto.conexaoId, contato_ids: dto.contatoIds };
    return this.http.post<any>(this.api, payload).pipe(map(c => this._normalizar(c)));
  }

  deletar(id: number): Observable<void> {
    return this.http.delete<void>(`${this.api}/${id}`);
  }

  disparar(id: number): Observable<Campanha> {
    return this.http.post<any>(`${this.api}/${id}/disparar`, {}).pipe(map(c => this._normalizar(c)));
  }

  private _normalizar(raw: any): Campanha {
    return {
      id: raw.id,
      nome: raw.nome,
      mensagem: raw.mensagem,
      conexaoId: raw.conexao_id ?? raw.conexaoId,
      status: raw.status,
      totalContatos: raw.total_contatos ?? raw.totalContatos ?? 0,
      enviados: raw.enviados ?? 0,
      falhas: raw.falhas ?? 0,
      criadoEm: raw.criado_em ?? raw.criadoEm,
      enviadoEm: raw.enviado_em ?? raw.enviadoEm,
    };
  }

  private _normalizarDetalhe(raw: any): CampanhaDetalhe {
    return {
      ...this._normalizar(raw),
      contatos: (raw.contatos ?? []).map((it: any) => ({
        id: it.id,
        contatoId: it.contato_id ?? it.contatoId,
        status: it.status,
        erroMensagem: it.erro_mensagem ?? it.erroMensagem,
        enviadoEm: it.enviado_em ?? it.enviadoEm,
        contato: it.contato,
      })),
    };
  }
}
