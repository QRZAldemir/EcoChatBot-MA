import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, map } from 'rxjs';
import { Menu, MenuOpcao } from '../models/menu.model';
import { environment } from '../../../environments/environment';

@Injectable({ providedIn: 'root' })
export class MenuService {
  private api = `${environment.apiUrl}/menus`;

  constructor(private http: HttpClient) {}

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

  // Envia o array de opções junto (com "id" nas que já existiam); o backend
  // resolve criação/atualização/remoção das opções na mesma transação do menu.
  atualizar(id: number, dto: Partial<Menu>): Observable<Menu> {
    return this.http.put<Menu>(`${this.api}/${id}`, this._serializar(dto)).pipe(map(m => this._normalizar(m)));
  }

  deletar(id: number): Observable<void> {
    return this.http.delete<void>(`${this.api}/${id}`);
  }

  private _normalizar(raw: any): Menu {
    return {
      ...raw,
      textoBotao: raw.texto_botao ?? raw.textoBotao,
      canalId: raw.canal_id ?? raw.canalId,
      usuarioVinculadoId: raw.usuario_vinculado_id ?? raw.usuarioVinculadoId,
      usuarioVinculadoNome: raw.usuario_vinculado_nome ?? raw.usuarioVinculadoNome,
      criadoEm: raw.criado_em ?? raw.criadoEm,
      opcoes: (raw.opcoes ?? []).map((o: any) => ({
        ...o,
        menuId: o.menu_id ?? o.menuId,
        rowId: o.row_id ?? o.rowId,
      })),
    };
  }

  private _serializar(dto: Partial<Menu>): Record<string, unknown> {
    const { textoBotao, canalId, usuarioVinculadoId, usuarioVinculadoNome, criadoEm, opcoes, ...rest } = dto as any;
    return {
      ...rest,
      ...(textoBotao !== undefined && { texto_botao: textoBotao }),
      ...(canalId !== undefined && { canal_id: canalId }),
      ...(usuarioVinculadoId !== undefined && { usuario_vinculado_id: usuarioVinculadoId }),
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
