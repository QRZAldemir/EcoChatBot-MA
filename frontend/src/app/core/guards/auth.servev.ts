import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { NivelAcesso } from '../models/nivel-usuario.model';
import { AuthService } from '../services/auth.service';
import { temNivelMinimo } from '../auth/niveis';

/** Bloqueia a rota se o nível do usuário logado for abaixo de `data.nivelMinimo`. */
export const nivelGuard: CanActivateFn = (route) => {
  const auth = inject(AuthService);
  const router = inject(Router);
  const minimo = route.data['nivelMinimo'] as NivelAcesso | undefined;

  if (temNivelMinimo(auth.getUsuarioAtual()?.nivel, minimo)) {
    return true;
  }

  router.navigate(['/admin/dashboard']);
  return false;
};
