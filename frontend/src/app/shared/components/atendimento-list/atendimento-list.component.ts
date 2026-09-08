import { CommonModule } from '@angular/common';
import { Component, Input } from '@angular/core';

export interface Atendimento {
  protocolo: string;
  nomeContato?: string;
  nome?: string;
  status: string;
}

@Component({
  selector: 'app-atendimento-list',
  standalone: true,
  imports: [CommonModule],
  template: `
      <div class="list-card">
        <h4>Atendimentos</h4>
        <div *ngIf="!atendimentos?.length" class="empty">Nenhum atendimento encontrado.</div>
        <ul *ngIf="atendimentos?.length">
          <li *ngFor="let item of atendimentos">
            <strong>{{ item.protocolo }}</strong>
            <span>{{ item.nomeContato || item.nome || 'Sem nome' }}</span>
            <small>{{ item.status }}</small>
          </li>
        </ul>
      </div>
      `
  ,
  styles: [
    ':host { display: block; }',
    '.list-card { background: #fff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 16px; }',
    'h4 { margin: 0 0 12px; }',
    'ul { list-style: none; padding: 0; margin: 0; display: grid; gap: 10px; }',
    'li { display: flex; justify-content: space-between; gap: 12px; border-bottom: 1px solid #f3f4f6; padding-bottom: 8px; }',
    '.empty { color: #6b7280; }'
  ]
})
export class AtendimentoListComponent {
  @Input() atendimentos: Atendimento[] = [];
}
