import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { SelectOption } from '../../../../models/common.model';

export interface FilterOptions {
    departamentos: SelectOption[];
    atendentes: SelectOption[];
    status: SelectOption[];
}

export interface FilterValues {
    departamento?: string;
    atendente?: string;
    status?: string;
    dataIni?: Date;
    dataFim?: Date;
    search?: string;
}

@Component({
    selector: 'app-filter-bar',
    standalone: true,
    imports: [CommonModule, FormsModule],
    template: `
    <div class="filter-bar">
      <label>
        Departamento
        <select [(ngModel)]="filters.departamento">
          <option value="">Todos</option>
          <option *ngFor="let item of options.departamentos" [value]="item.nome">{{ item.nome }}</option>
        </select>
      </label>
      <label>
        Atendente
        <select [(ngModel)]="filters.atendente">
          <option value="">Todos</option>
          <option *ngFor="let item of options.atendentes" [value]="item.nome">{{ item.nome }}</option>
        </select>
      </label>
      <label>
        Status
        <select [(ngModel)]="filters.status">
          <option value="">Todos</option>
          <option *ngFor="let item of options.status" [value]="item.id">{{ item.nome }}</option>
        </select>
      </label>
      <button type="button" (click)="applyFilters()">Aplicar</button>
      <button type="button" class="secondary" (click)="clearFilters()">Limpar</button>
    </div>
  `,
    styles: [
        '.filter-bar { display: flex; flex-wrap: wrap; gap: 12px; background: #fff; border: 1px solid #e5e7eb; padding: 12px; border-radius: 12px; }',
        'label { display: grid; gap: 6px; font-size: 12px; color: #4b5563; }',
        'select, button { height: 38px; border-radius: 8px; border: 1px solid #d1d5db; padding: 0 10px; }',
        'button { background: #111827; color: white; cursor: pointer; }',
        '.secondary { background: transparent; color: #111827; }'
    ]
})
export class FilterBarComponent {
    @Input() options: FilterOptions = { departamentos: [], atendentes: [], status: [] };
    @Output() filterApplied = new EventEmitter<FilterValues>();
    @Output() filterCleared = new EventEmitter<void>();

    filters: FilterValues = {};

    applyFilters(): void {
        this.filterApplied.emit(this.filters);
    }

    clearFilters(): void {
        this.filters = {};
        this.filterCleared.emit();
    }
}
