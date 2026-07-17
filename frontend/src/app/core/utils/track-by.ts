/**
 * trackBy compartilhado para *ngFor sobre listas de entidades (id numérico ou string).
 * Uma única referência de função reutilizada por todos os componentes: evita que o
 * Angular recrie os nós do DOM quando a lista é substituída mas os itens continuam
 * os mesmos (menos alocação, menos trabalho de change detection).
 */
export function trackById<T extends { id: number | string }>(_index: number, item: T): number | string {
  return item.id;
}
