import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, map, of } from 'rxjs';
import { Arquivo } from '../models/arquivo.model';
import { environment } from '../../../environments/environment';

@Injectable({ providedIn: 'root' })
export class ArquivoService {
  private api = `${environment.apiUrl}/arquivos`;

  constructor(private http: HttpClient) { }

  listar(): Observable<Arquivo[]> {
    return this.http.get<any[]>(this.api).pipe(map(as => as.map(a => this._normalizar(a))));
  }

  enviar(arquivo: File, descricao?: string): Observable<Arquivo> {
    const form = new FormData();
    form.append('arquivo', arquivo);
    if (descricao) form.append('descricao', descricao);
    return this.http.post<any>(this.api, form).pipe(map(a => this._normalizar(a)));
  }

  lerExcel(file: File): Observable<any[]> {
    if (!file || !file.name.toLowerCase().includes('.xlsx')) {
      return of([]);
    }

    return of([]);
  }

  deletar(id: number): Observable<void> {
    return this.http.delete<void>(`${this.api}/${id}`);
  }

  downloadUrl(id: number): string {
    return `${this.api}/${id}/download`;
  }

  private _normalizar(raw: any): Arquivo {
    return {
      id: raw.id,
      nomeOriginal: raw.nome_original ?? raw.nomeOriginal,
      tipoMime: raw.tipo_mime ?? raw.tipoMime,
      tamanhoBytes: raw.tamanho_bytes ?? raw.tamanhoBytes,
      descricao: raw.descricao,
      atendimentoId: raw.atendimento_id ?? raw.atendimentoId,
      criadoEm: raw.criado_em ?? raw.criadoEm,
    };
  }
}
