import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, map, tap } from 'rxjs';
import { environment } from '../../../environments/environment';
import { LoginResponse, UsuarioLogado } from '../models/auth.model';

const CHAVE_TOKEN = 'ecochat_token';
const CHAVE_USUARIO = 'ecochat_usuario';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private api = `${environment.apiUrl}/auth`;

  constructor(private http: HttpClient) {}

  login(email: string, senha: string): Observable<LoginResponse> {
    return this.http.post<any>(`${this.api}/login`, { email, senha }).pipe(
      // O backend retorna usuario.departamento_id/canal_id em snake_case;
      // sem normalizar aqui, UsuarioLogado.departamentoId/canalId ficam
      // sempre undefined e nada que dependa do setor do atendente logado
      // (ex: painel de atendimentos) funciona.
      map(resp => ({
        ...resp,
        usuario: {
          ...resp.usuario,
          departamentoId: resp.usuario?.departamento_id ?? resp.usuario?.departamentoId,
          canalId: resp.usuario?.canal_id ?? resp.usuario?.canalId,
        },
      }) as LoginResponse),
      tap(resp => {
        localStorage.setItem(CHAVE_TOKEN, resp.access_token);
        localStorage.setItem(CHAVE_USUARIO, JSON.stringify(resp.usuario));
      }),
    );
  }

  logout(): void {
    localStorage.removeItem(CHAVE_TOKEN);
    localStorage.removeItem(CHAVE_USUARIO);
  }

  getToken(): string | null {
    return localStorage.getItem(CHAVE_TOKEN);
  }

  getUsuarioAtual(): UsuarioLogado | null {
    const raw = localStorage.getItem(CHAVE_USUARIO);
    return raw ? JSON.parse(raw) : null;
  }

  isAuthenticated(): boolean {
    return !!this.getToken();
  }
}
