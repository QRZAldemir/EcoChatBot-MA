// frontend/src/app/core/guards/auth.guard.ts
import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';
import { Observable, of } from 'rxjs';
import { map, take, catchError } from 'rxjs/operators';

export const authGuard: CanActivateFn = (): Observable<boolean> => {
  const authService = inject(AuthService);
  const router = inject(Router);

  // Verificação rápida do token local
  const token = authService.getToken();
  if (!token) {
    router.navigate(['/login']);
    return of(false);
  }

  // Validação do token no servidor
  return authService.validateToken(token).pipe(
    take(1),
    map(isValid => {
      if (!isValid) {
        authService.clearSession();
        router.navigate(['/login']);
        return false;
      }
      return true;
    }),
    catchError(() => {
      authService.clearSession();
      router.navigate(['/login']);
      return of(false);
    })
  );
};
