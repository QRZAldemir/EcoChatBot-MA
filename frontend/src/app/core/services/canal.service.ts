import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Canal } from '../models/canal.model';
import { environment } from '../../../environments/environment';

@Injectable({ providedIn: 'root' })
export class CanalService {
  private api = `${environment.apiUrl}/canais`;

  constructor(private http: HttpClient) {}

  listar(): Observable<Canal[]> {
    return this.http.get<Canal[]>(this.api);
  }

  buscarPorId(id: number): Observable<Canal> {
    return this.http.get<Canal>(`${this.api}/${id}`);
  }

  criar(dto: Partial<Canal>): Observable<Canal> {
    return this.http.post<Canal>(this.api, dto);
  }

  atualizar(id: number, dto: Partial<Canal>): Observable<Canal> {
    return this.http.put<Canal>(`${this.api}/${id}`, dto);
  }

  deletar(id: number): Observable<void> {
    return this.http.delete<void>(`${this.api}/${id}`);
  }

  // Retorna URL do menu do canal (iframe ou rota interna futura)
  getUrlMenu(canal: Canal): string {
    return `${environment.menusBaseUrl}/${canal.arquivoMenu}`;
  }
}
