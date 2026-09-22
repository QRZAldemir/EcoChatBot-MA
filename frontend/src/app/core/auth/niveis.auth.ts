import { NivelAcesso } from '../models/nivel-usuario.model';

/** Mesma hierarquia de `app/security.py`: atendente < supervisor < gerente < administrador. */
export const NIVEIS_HIERARQUIA: NivelAcesso[] = [
  'atendente',
  'supervisor',
  'gerente',
  'administrador',
];

export function ordemNivel(nivel?: string | null): number {
  return NIVEIS_HIERARQUIA.indexOf((nivel || '').toLowerCase() as NivelAcesso);
}

/** Sem `minimo`, qualquer usuário autenticado passa. Nível desconhecido não passa de nenhum piso. */
export function temNivelMinimo(nivel: string | undefined | null, minimo?: NivelAcesso): boolean {
  if (!minimo) return true;
  return ordemNivel(nivel) >= ordemNivel(minimo);
}
