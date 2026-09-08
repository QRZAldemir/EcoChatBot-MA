import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

export interface Stats {
  total?: number;
  humanos?: number;
  robos?: number;
  emAberto?: number;
  tma?: number;
  tme?: number;
}

@Component({
  selector: 'app-stats-cards',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './stats-cards.component.html',
  styleUrls: ['./stats-cards.component.css']
})
export class StatsCardsComponent {
  @Input() stats: Stats = { total: 0 };

  get pctHumanos(): string {
    if (!this.stats.total || this.stats.total === 0) return '0%';
    const pct = Math.round(((this.stats.humanos || 0) / this.stats.total) * 100);
    return pct + '%';
  }

  get tmaFormatado(): string {
    const min = this.stats.tma;
    if (!min || min < 1) return '—';
    if (min < 60) return Math.round(min) + ' min';
    const h = Math.floor(min / 60);
    const m = Math.round(min % 60);
    return h + 'h ' + m + 'min';
  }

  get tmeFormatado(): string {
    const min = this.stats.tme;
    if (!min || min < 1) return '—';
    if (min < 60) return Math.round(min) + ' min';
    const h = Math.floor(min / 60);
    const m = Math.round(min % 60);
    return h + 'h ' + m + 'min';
  }
}