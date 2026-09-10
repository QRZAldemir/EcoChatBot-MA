================================================================================
SKILL: ENGENHARIA DE SEGURANÇA DE IDENTIDADE E PROTEÇÃO DE DADOS
ARQUIVO: skill_engenharia_seguranca_identidade.txt
VERSÃO: 3.0.0
STACK:
  BACKEND  : Python 3.12+ (FastAPI, PyJWT, passlib[bcrypt], Alembic, slowapi, redis)
  FRONTEND : Angular 17+ (interceptors funcionais, guards, RxJS)
OBSERVAÇÃO: Revisão sem qualquer tecnologia Java; toda a orquestração de
segurança é nativa do ecossistema Python.
================================================================================

--------------------------------------------------------------------------------
1. METADADOS
--------------------------------------------------------------------------------
name    : engenharia-seguranca-identidade
version : 3.0.0
triggers:
  - implementar autenticação ou autorização
  - emitir, validar ou revogar JWT
  - configurar segurança de API Python (FastAPI)
  - armazenar ou migrar senhas (hashing BCrypt)
  - integrar Auth0 / IDaaS
  - revisar segurança de API (LGPD, OWASP)
principios:
  - Security by Design
  - Tríade CIA (Confidencialidade, Integridade, Disponibilidade)
  - Separação entre autenticação e autorização
  - Princípio do Menor Privilégio (PoLP)
  - JWT stateless com revogação
  - Defesa em profundidade (backend autoritativo; Angular protege apenas a UX)

--------------------------------------------------------------------------------
2. MAPEAMENTO DAS TÉCNICAS DO GUIA -> COMPONENTES
--------------------------------------------------------------------------------
Tríade CIA (Confid./Integ./Disponib.)  -> Dependências de escopo, HMAC-SHA256, slowapi
SQL Injection / XSS                    -> SQLAlchemy parametrizado; sanitização Angular
Autenticação ("quem é você")           -> OAuth2PasswordBearer + BCrypt (passlib)
Autorização / Roles / PoLP             -> exigir_role() via Depends
JWT stateless                          -> jwt_service.py (PyJWT; require: exp/iss/aud/sub)
Revogação de tokens                    -> Denylist em Redis (redis.asyncio)
Hashing + migração segura              -> passlib/bcrypt + Alembic
Rate Limiting (DDoS)                   -> slowapi
IDaaS / Auth0                          -> python-jose com JWKS (RS256)
Monitoramento                          -> Bandit, Safety/pip-audit, Sonar/Veracode

--------------------------------------------------------------------------------
3. FLUXO DE EXECUÇÃO
--------------------------------------------------------------------------------
FASE 1 - modelar_ameacas    : matriz de ameaças por endpoint; controles
                              server-side (ORM parametrizado, validação de
                              entrada) e client-side (sanitização, CSP).
FASE 2 - definir_identidade : roles nos claims; PoLP aplicado no backend via
                              Depends(exigir_role(...)); guards Angular só UX.
FASE 3 - implementar_jwt    : emissão/validação via PyJWT; payload sem dados
                              sensíveis; revogação via Denylist Redis ou
                              Refresh Token em cookie httpOnly.
FASE 4 - orquestrar_seguranca: middlewares (cabeçalhos, CORS) + dependências de
                              autenticação; migração de credenciais via Alembic
                              sem perda de histórico.
FASE 5 - integrar_idaas     : validação de tokens Auth0 via JWKS/RS256;
                              frontend com Authorization Code + PKCE.
FASE 6 - auditar_seguranca  : checklist da Seção 6 com análise estática
                              (Bandit, Safety, Sonar/Veracode) no CI.

--------------------------------------------------------------------------------
4. REFERÊNCIAS TÉCNICAS - BACKEND (PYTHON)
--------------------------------------------------------------------------------

--- ARQUIVO: backend_python/jwt_service.py -------------------------------------
import os
from datetime import datetime, timedelta, timezone
import jwt
from passlib.context import CryptContext

ALGORITMO = "HS256"                                    # RS256 com par de chaves, se preferido
CHAVE_SECRETA = os.environ["JWT_SECRET"]              # Vault/env - jamais no Git
EMISSOR = os.environ.get("JWT_ISSUER", "api-sistema")
AUDIENCIA = os.environ.get("JWT_AUDIENCE", "app-angular")
EXPIRACAO_MIN = int(os.environ.get("JWT_EXPIRATION_MIN", "15"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_senha(senha: str) -> str:
    return pwd_context.hash(senha, rounds=12)

def verificar_senha(senha: str, hash_armazenado: str) -> bool:
    return pwd_context.verify(senha, hash_armazenado)

def emitir_token(usuario: dict) -> str:
    agora = datetime.now(timezone.utc)
    return jwt.encode({
        "sub": usuario["username"],
        "roles": usuario["roles"],        # autorização; nenhum dado sensível no payload
        "iss": EMISSOR,
        "aud": AUDIENCIA,
        "iat": agora,
        "exp": agora + timedelta(minutes=EXPIRACAO_MIN),
    }, CHAVE_SECRETA, algorithm=ALGORITMO)

def validar_token(token: str) -> dict:
    return jwt.decode(token, CHAVE_SECRETA, algorithms=[ALGORITMO],
                      issuer=EMISSOR, audience=AUDIENCIA,
                      options={"require": ["exp", "iss", "aud", "sub"]})

--- ARQUIVO: backend_python/dependencias.py ------------------------------------
import os
import jwt as pyjwt
import redis.asyncio as redis
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from app.security.jwt_service import validar_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
_redis = redis.from_url(os.environ["REDIS_URL"])

async def obter_usuario_atual(token: str = Depends(oauth2_scheme)) -> dict:
    try:
        payload = validar_token(token)
    except pyjwt.PyJWTError as exc:
        raise HTTPException(401, "Token inválido ou expirado") from exc
    if await _redis.exists(f"denylist:{token}"):
        raise HTTPException(401, "Token revogado")
    return payload

def exigir_role(role: str):
    """Autorização declarativa (PoLP)."""
    async def _verificador(usuario: dict = Depends(obter_usuario_atual)) -> dict:
        if role not in usuario.get("roles", []):
            raise HTTPException(403, "Privilégio insuficiente")
        return usuario
    return _verificador

async def revogar_token(token: str, expira_em_s: int) -> None:
    await _redis.setex(f"denylist:{token}", expira_em_s, "1")

--- ARQUIVO: backend_python/middleware.py --------------------------------------
from starlette.middleware.base import BaseHTTPMiddleware

class CabecalhosSegurancaMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        resposta = await call_next(request)
        resposta.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        resposta.headers["Content-Security-Policy"] = "default-src 'self'"
        resposta.headers["X-Content-Type-Options"] = "nosniff"
        resposta.headers["X-Frame-Options"] = "DENY"
        resposta.headers["Referrer-Policy"] = "no-referrer"
        return resposta

--- ARQUIVO: backend_python/integridade.py -------------------------------------
import base64, hashlib, hmac, os

CHAVE_HMAC = os.environ["HMAC_SECRET"].encode()

def assinar_payload(payload: str) -> str:
    return base64.b64encode(
        hmac.new(CHAVE_HMAC, payload.encode(), hashlib.sha256).digest()
    ).decode()

def verificar_assinatura(payload: str, assinatura: str) -> bool:
    return hmac.compare_digest(assinar_payload(payload), assinatura)

--- ARQUIVO: backend_python/main.py ---------------------------------------------
import os
from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from app.security.middleware import CabecalhosSegurancaMiddleware
from app.security.dependencias import (obter_usuario_atual, exigir_role,
                                       revogar_token, oauth2_scheme)
from app.security.jwt_service import emitir_token, verificar_senha

app = FastAPI(title="API Segura")
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(CabecalhosSegurancaMiddleware)
app.add_middleware(CORSMiddleware,
                   allow_origins=[os.environ["FRONTEND_URL"]],  # somente o domínio Angular
                   allow_credentials=True,
                   allow_methods=["GET", "POST", "PUT", "DELETE"],
                   allow_headers=["Authorization"])

@app.post("/auth/login")
@limiter.limit("5/minute")                              # mitiga força bruta/DDoS
async def login(request: Request, cred: OAuth2PasswordRequestForm):
    usuario = repo.buscar_por_username(cred.username)
    if not usuario or not verificar_senha(cred.password, usuario.password):
        raise HTTPException(401, "Credenciais inválidas")   # resposta genérica
    return {"access_token": emitir_token(usuario), "token_type": "bearer"}

@app.post("/auth/refresh")
async def refresh(request: Request):
    # Refresh Token em cookie httpOnly + SameSite=Strict
    refresh_token = request.cookies.get("refresh_token")
    novo_refresh = await repo.validar_e_rotacionar_refresh(refresh_token)
    if not novo_refresh:
        raise HTTPException(401, "Refresh inválido")
    resposta = JSONResponse({"access_token": emitir_token(novo_refresh.usuario),
                             "token_type": "bearer"})
    resposta.set_cookie("refresh_token", novo_refresh.valor, httponly=True,
                        samesite="strict", secure=True, max_age=novo_refresh.expira_em_s)
    return resposta

@app.post("/auth/logout")
async def logout(token: str = Depends(oauth2_scheme),
                 usuario: dict = Depends(obter_usuario_atual)):
    await revogar_token(token, expira_em_s=900)
    return {"status": "sessão encerrada"}

@app.get("/admin/configuracoes", dependencies=[Depends(exigir_role("ADMIN"))])
async def configuracoes():
    ...

@app.get("/transacoes/{transacao_id}")                  # Confidencialidade - anti-IDOR
async def buscar_transacao(transacao_id: int,
                           usuario: dict = Depends(obter_usuario_atual)):
    transacao = repo.buscar(transacao_id)
    if transacao.cliente_id != usuario["sub"]:
        raise HTTPException(403, "Escopo inválido")
    return transacao

--- ARQUIVO: backend_python/migracao_alembic.py ---------------------------------
"""Adicionar password hash (BCrypt) sem perda de histórico.

Revision ID: 20260807_01
"""
import sqlalchemy as sa
from alembic import op

revision = "20260807_01"
down_revision = "20260801_01"

def upgrade():
    op.add_column("usuarios", sa.Column("password", sa.String(60)))
    op.add_column("usuarios", sa.Column("senha_reset_pendente",
                sa.Boolean(), server_default="true", nullable=False))
    op.execute("UPDATE usuarios SET password = '<hash_bcrypt_temporario>' "
               "WHERE password IS NULL")
    op.alter_column("usuarios", "password", nullable=False)  # integridade de esquema

def downgrade():
    op.drop_column("usuarios", "senha_reset_pendente")
    op.drop_column("usuarios", "password")

--- ARQUIVO: backend_python/auth0.py ---------------------------------------------
import json, os
from urllib.request import urlopen
from jose import jwt as jose_jwt
from jose.exceptions import JOSEError
from fastapi import HTTPException

DOMAIN = os.environ["AUTH0_DOMAIN"]          # segredos via env; nunca no Git
AUDIENCE = os.environ["AUTH0_AUDIENCE"]
JWKS = json.load(urlopen(f"https://{DOMAIN}/.well-known/jwks.json"))

def validar_token_auth0(token: str) -> dict:
    try:
        header = jose_jwt.get_unverified_header(token)
        chave = next(k for k in JWKS["keys"] if k["kid"] == header["kid"])
        return jose_jwt.decode(token, chave, algorithms=["RS256"],
                               audience=AUDIENCE, issuer=f"https://{DOMAIN}/")
    except (JOSEError, StopIteration) as exc:
        raise HTTPException(401, "Token Auth0 inválido") from exc

--------------------------------------------------------------------------------
5. REFERÊNCIAS TÉCNICAS - FRONTEND (ANGULAR)
--------------------------------------------------------------------------------

--- ARQUIVO: frontend_angular/auth.service.ts -----------------------------------
import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable } from 'rxjs';
import { tap } from 'rxjs/operators';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private http = inject(HttpClient);
  private tokenSubject = new BehaviorSubject<string | null>(null);  // só em memória
  readonly token$ = this.tokenSubject.asObservable();

  login(usuario: string, senha: string): Observable<void> {
    return this.http
      .post<{ access_token: string }>('/auth/login',
        { username: usuario, password: senha })
      .pipe(tap(res => this.armazenarToken(res.access_token)));
  }

  get token(): string | null { return this.tokenSubject.value; }

  armazenarToken(token: string): void { this.tokenSubject.next(token); }

  roles(): string[] {
    const token = this.token;
    if (!token) { return []; }
    const payload = JSON.parse(atob(token.split('.')[1]));  // Base64 - apenas UX
    return payload['roles'] ?? [];
  }

  logout(): void { this.tokenSubject.next(null); }
}

--- ARQUIVO: frontend_angular/refresh.service.ts --------------------------------
import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { AuthService } from './auth.service';

@Injectable({ providedIn: 'root' })
export class RefreshService {
  private http = inject(HttpClient);
  private auth = inject(AuthService);

  // cookie httpOnly é enviado automaticamente via withCredentials
  refresh(): Observable<string> {
    return this.http
      .post<{ access_token: string }>('/auth/refresh', {}, { withCredentials: true })
      .pipe(map(res => {
        this.auth.armazenarToken(res.access_token);
        return res.access_token;
      }));
  }
}

--- ARQUIVO: frontend_angular/auth.interceptor.ts -------------------------------
import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, switchMap, throwError } from 'rxjs';
import { AuthService } from './auth.service';
import { RefreshService } from './refresh.service';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const auth = inject(AuthService);
  const refresh = inject(RefreshService);

  const anexar = (token: string | null) =>
    token ? req.clone({ setHeaders: { Authorization: `Bearer ${token}` } }) : req;

  return next(anexar(auth.token)).pipe(
    catchError((erro: HttpErrorResponse) =>
      erro.status === 401 && !req.url.includes('/auth/')
        ? refresh.refresh().pipe(switchMap(t => next(anexar(t))))
        : throwError(() => erro))
  );
};

--- ARQUIVO: frontend_angular/auth.guard.ts --------------------------------------
import { CanActivateFn, Router } from '@angular/router';
import { inject } from '@angular/core';
import { AuthService } from './auth.service';

export const authGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);
  return auth.token ? true : router.parseUrl('/login');
};

export const adminGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);
  return auth.roles().includes('ADMIN') ? true : router.parseUrl('/');
};

--- ARQUIVO: frontend_angular/app.routes.ts ---------------------------------------
import { Routes } from '@angular/router';
import { authGuard, adminGuard } from './core/auth/auth.guard';

export const routes: Routes = [
  { path: 'login',
    loadComponent: () => import('./login/login.component').then(c => c.LoginComponent) },
  { path: 'admin', canActivate: [authGuard, adminGuard],
    loadComponent: () => import('./admin/admin.component').then(c => c.AdminComponent) },
  { path: 'transacoes', canActivate: [authGuard],
    loadComponent: () =>
      import('./transacoes/transacoes.component').then(c => c.TransacoesComponent) },
  { path: '**', redirectTo: 'login' },
];

--- ARQUIVO: frontend_angular/app.config.ts ----------------------------------------
import { ApplicationConfig } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { routes } from './app.routes';
import { authInterceptor } from './core/auth/auth.interceptor';

export const appConfig: ApplicationConfig = {
  providers: [
    provideRouter(routes),
    provideHttpClient(withInterceptors([authInterceptor])),
  ],
};

DIRETIVAS DE CLIENTE:
  - Token de acesso somente em memória (proibido localStorage, devido a XSS).
  - Refresh Token em cookie httpOnly + SameSite=Strict + Secure.
  - Confiar na sanitização nativa do Angular; evitar bypassSecurityTrust*.

--------------------------------------------------------------------------------
6. CHECKLIST INEGOCIÁVEL
--------------------------------------------------------------------------------
01. HTTPS + HSTS (MitM)            -> cabeçalho do middleware; TLS em produção
02. BCrypt (rounds >= 12)          -> revisão de jwt_service.py; coluna VARCHAR(60)
03. JWT: assinatura, iss, aud, exp -> testes com token adulterado/expirado
04. PoLP: exigir_role + guards     -> testes de escalada; backend autoritativo
05. Anti-IDOR (escopo próprio)     -> testes de travessia entre clientes
06. Revogação (Denylist Redis)     -> logout com token reapresentado deve falhar
07. Rate limiting (slowapi)        -> testes de carga / simulação de DDoS
08. Segredos em Vault/env          -> varredura de repositório (sem secrets no Git)
09. Migração Alembic sem perda     -> execução em staging; nullable=False ao final
10. Análise estática contínua      -> Bandit, Safety/pip-audit, Sonar/Veracode no CI

--------------------------------------------------------------------------------
7. ESTRUTURA DE ARQUIVOS DA SKILL
--------------------------------------------------------------------------------
skills/
└── engenharia-seguranca-identidade/
    ├── SKILL.md
    └── references/
        ├── backend_python/
        │   ├── jwt_service.py
        │   ├── dependencias.py
        │   ├── middleware.py
        │   ├── integridade.py
        │   ├── main.py
        │   ├── migracao_alembic.py
        │   └── auth0.py
        └── frontend_angular/
            ├── auth.service.ts
            ├── refresh.service.ts
            ├── auth.interceptor.ts
            ├── auth.guard.ts
            ├── app.routes.ts
            └── app.config.ts

--------------------------------------------------------------------------------
8. NOTAS FINAIS
--------------------------------------------------------------------------------
- Esta skill não utiliza qualquer tecnologia Java; a orquestração de segurança
  é integralmente implementada em Python (FastAPI) com Angular no frontend.
- A segurança é um processo de vigilância contínua: executar o checklist a
  cada entrega e monitorar tentativas de acesso anômalas.
- Conformidade alvo: LGPD, OAuth2/OIDC, OWASP.
================================================================================