import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

export interface FilterOptions {
  departamentos: Array<{ id: number | string; nome: string }>;
}

export interface FilterValues {
  departamento?: string;
  search?: string;
}

@Component({
  selector: 'app-filter-bar',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './filter-bar.component.html',
  styleUrls: ['./filter-bar.component.css']
})
export class FilterBarComponent {
  @Input() options: FilterOptions = { departamentos: [] };
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
