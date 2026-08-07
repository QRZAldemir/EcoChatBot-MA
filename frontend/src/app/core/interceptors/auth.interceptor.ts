import { inject } from '@angular/core';
import { HttpInterceptorFn } from '@angular/common/http';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';
import { AuthService } from '../services/auth.service';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const auth = inject(AuthService);
  const router = inject(Router);
  const token = auth.getToken();

  const request = token ? req.clone({ setHeaders: { Authorization: `Bearer ${token}` } }) : req;

  return next(request).pipe(
    catchError(err => {
      // 401 numa rota protegida = sessão expirada/revogada — exceto no
      // próprio /auth/login, onde 401 é "credenciais inválidas" e deve
      // ser tratado pelo formulário de login, não aqui. Usa limpeza local
      // (sem chamar /logout de novo) para não repetir o mesmo 401 em loop.
      if (err.status === 401 && !req.url.includes('/auth/login')) {
        auth.limparSessaoLocal();
        router.navigate(['/login']);
      }
      return throwError(() => err);
    }),
  );
};
