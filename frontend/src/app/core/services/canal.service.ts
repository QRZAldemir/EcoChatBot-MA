import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, map } from 'rxjs';
import { Canal } from '../models/canal.model';
import { environment } from '../../../environments/environment';

const ICONE_MAP: Record<string, string> = {
  '1atendimento-ma.html':       '📞',
  '2agendamento-ma.html':        '📅',
  '3examesdiagnostico-ma.html':  '🩺',
  '7portaria-ma.html':           '🚪',
  '8ouvidoria-ma.html':          '📢',
};

@Injectable({ providedIn: 'root' })
export class CanalService {
  private api = `${environment.apiUrl}/canais`;

  constructor(private http: HttpClient) {}

  listar(): Observable<Canal[]> {
    return this.http.get<Canal[]>(this.api).pipe(map(cs => cs.map(c => this._normalizar(c))));
  }

  buscarPorId(id: number): Observable<Canal> {
    return this.http.get<Canal>(`${this.api}/${id}`).pipe(map(c => this._normalizar(c)));
  }

  criar(dto: Partial<Canal>): Observable<Canal> {
    return this.http.post<Canal>(this.api, this._serializar(dto)).pipe(map(c => this._normalizar(c)));
  }

  atualizar(id: number, dto: Partial<Canal>): Observable<Canal> {
    return this.http.put<Canal>(`${this.api}/${id}`, this._serializar(dto)).pipe(map(c => this._normalizar(c)));
  }

  deletar(id: number): Observable<void> {
    return this.http.delete<void>(`${this.api}/${id}`);
  }

  getUrlMenu(canal: Canal): string {
    return `${environment.menusBaseUrl}/${canal.arquivoMenu}`;
  }

  // Converte snake_case do backend → camelCase + atribui ícone padrão
  private _normalizar(raw: any): Canal {
    const arquivo = raw.arquivo_menu ?? raw.arquivoMenu ?? '';
    return {
      ...raw,
      arquivoMenu: arquivo,
      icone: raw.icone ?? ICONE_MAP[arquivo] ?? '📋',
      departamentoId: raw.departamento_id ?? raw.departamentoId,
      departamentoNome: raw.departamento?.nome ?? raw.departamentoNome,
      criadoEm: raw.criado_em ?? raw.criadoEm,
    };
  }

  // Converte camelCase do frontend → snake_case para enviar ao backend
  private _serializar(dto: Partial<Canal>): Record<string, unknown> {
    const { arquivoMenu, departamentoId, criadoEm, icone, cor, ...rest } = dto as any;
    return {
      ...rest,
      ...(arquivoMenu !== undefined   && { arquivo_menu: arquivoMenu }),
      ...(departamentoId !== undefined && { departamento_id: departamentoId }),
    };
  }
}
