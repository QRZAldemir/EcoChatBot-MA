import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, map } from 'rxjs';
import { Menu, MenuOpcao } from '../models/menu.model';
import { environment } from '../../../environments/environment';

@Injectable({ providedIn: 'root' })
export class MenuService {
  private api = `${environment.apiUrl}/menus`;

  constructor(private http: HttpClient) { }

  listar(canalId?: number, apenasAtivos = false): Observable<Menu[]> {
    let params: Record<string, string> = {};
    if (canalId !== undefined) params['canal_id'] = String(canalId);
    if (apenasAtivos) params['apenas_ativos'] = 'true';
    return this.http.get<Menu[]>(this.api, { params }).pipe(map(ms => ms.map(m => this._normalizar(m))));
  }

  buscarPorId(id: number): Observable<Menu> {
    return this.http.get<Menu>(`${this.api}/${id}`).pipe(map(m => this._normalizar(m)));
  }

  criar(dto: Partial<Menu>): Observable<Menu> {
    return this.http.post<Menu>(this.api, this._serializar(dto)).pipe(map(m => this._normalizar(m)));
  }

  atualizar(id: number, dto: Partial<Menu>): Observable<Menu> {
    const { opcoes, ...campos } = this._serializar(dto);
    return this.http.put<Menu>(`${this.api}/${id}`, campos).pipe(map(m => this._normalizar(m)));
  }

  deletar(id: number): Observable<void> {
    return this.http.delete<void>(`${this.api}/${id}`);
  }

  // ── Opções (mensagem já criada — MenuUpdate não aceita array de opções) ──

  adicionarOpcao(menuId: number, opcao: Partial<MenuOpcao>): Observable<MenuOpcao> {
    return this.http.post<MenuOpcao>(`${this.api}/${menuId}/opcoes`, this._serializarOpcao(opcao));
  }

  atualizarOpcao(opcaoId: number, opcao: Partial<MenuOpcao>): Observable<MenuOpcao> {
    return this.http.put<MenuOpcao>(`${this.api}/opcoes/${opcaoId}`, this._serializarOpcao(opcao));
  }

  deletarOpcao(opcaoId: number): Observable<void> {
    return this.http.delete<void>(`${this.api}/opcoes/${opcaoId}`);
  }

  private _normalizar(raw: any): Menu {
    return {
      ...raw,
      textoBotao: raw.texto_botao ?? raw.textoBotao,
      canalId: raw.canal_id ?? raw.canalId,
      criadoEm: raw.criado_em ?? raw.criadoEm,
      opcoes: (raw.opcoes ?? []).map((o: any) => ({
        ...o,
        menuId: o.menu_id ?? o.menuId,
        rowId: o.row_id ?? o.rowId,
      })),
    };
  }

  private _serializar(dto: Partial<Menu>): Record<string, unknown> {
    const { textoBotao, canalId, criadoEm, opcoes, ...rest } = dto as any;
    return {
      ...rest,
      ...(textoBotao !== undefined && { texto_botao: textoBotao }),
      ...(canalId !== undefined && { canal_id: canalId }),
      ...(opcoes !== undefined && { opcoes: (opcoes as MenuOpcao[]).map(o => this._serializarOpcao(o)) }),
    };
  }

  private _serializarOpcao(opcao: Partial<MenuOpcao>): Record<string, unknown> {
    const { rowId, menuId, ...rest } = opcao as any;
    return {
      ...rest,
      ...(rowId !== undefined && { row_id: rowId }),
    };
  }
}
