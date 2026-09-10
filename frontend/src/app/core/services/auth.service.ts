import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, map, tap } from 'rxjs';
import { environment } from '../../../environments/environment';
import { LoginResponse, UsuarioLogado } from '../models/auth.model';
import { NivelAcesso } from '../models/nivel-usuario.model';
import { temNivelMinimo } from '../auth/niveis';

const CHAVE_TOKEN = 'ecochat_token';
const CHAVE_USUARIO = 'ecochat_usuario';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private api = `${environment.apiUrl}/auth`;

  constructor(private http: HttpClient) { }

  login(email: string, senha: string): Observable<LoginResponse> {
    return this.http.post<any>(`${this.api}/login`, { email, senha }).pipe(
      map(resp => this._normalizar(resp)),
      tap(resp => this._salvarSessao(resp)),
    );
  }

  /** Renova o token antes de expirar, sem exigir login de novo. */
  refresh(): Observable<LoginResponse> {
    return this.http.post<any>(`${this.api}/refresh`, {}).pipe(
      map(resp => this._normalizar(resp)),
      tap(resp => this._salvarSessao(resp)),
    );
  }

  logout(): void {
    // Revoga o token no backend (JWT é stateless — sem isso ele continuaria
    // válido até expirar). Best-effort: a sessão local é limpa de qualquer forma.
    this.http.post(`${this.api}/logout`, {}).subscribe({ next: () => { }, error: () => { } });
    this.limparSessaoLocal();
  }

  /** Só limpa o storage local, sem chamar /logout — usado pelo interceptor ao reagir a um 401,
   *  onde chamar /logout de novo poderia recair no mesmo 401 (loop). */
  limparSessaoLocal(): void {
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
    const token = this.getToken();
    return !!token && !this.tokenExpirado(token);
  }

  temNivelMinimo(minimo: NivelAcesso): boolean {
    return temNivelMinimo(this.getUsuarioAtual()?.nivel, minimo);
  }

  /** Decodifica o payload do JWT (sem validar assinatura — isso é papel do backend) só para checar o "exp". */
  tokenExpirado(token: string): boolean {
    try {
      const payloadBase64 = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
      const payload = JSON.parse(atob(payloadBase64));
      return !payload.exp || payload.exp * 1000 <= Date.now();
    } catch {
      return true;
    }
  }

  private _salvarSessao(resp: LoginResponse): void {
    localStorage.setItem(CHAVE_TOKEN, resp.access_token);
    localStorage.setItem(CHAVE_USUARIO, JSON.stringify(resp.usuario));
  }

  private _normalizar(raw: any): LoginResponse {
    // O backend retorna usuario.departamento_id/canal_id em snake_case;
    // sem normalizar aqui, UsuarioLogado.departamentoId/canalId ficam
    // sempre undefined e nada que dependa do setor do atendente logado
    // (ex: painel de atendimentos) funciona.
    return {
      ...raw,
      usuario: {
        ...raw.usuario,
        departamentoId: raw.usuario?.departamento_id ?? raw.usuario?.departamentoId,
        canalId: raw.usuario?.canal_id ?? raw.usuario?.canalId,
      },
    } as LoginResponse;
  }
}
