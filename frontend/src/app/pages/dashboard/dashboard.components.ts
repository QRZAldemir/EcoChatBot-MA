import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { DashboardService } from '../../core/services/dashboard.service';
import { FilterBarComponent } from '../../shared/components/filter-bar/filter-bar.component';

@Component({
    selector: 'app-dashboard-page',
    standalone: true,
    imports: [CommonModule, RouterLink, FilterBarComponent],
    template: `
    <section class="page-dashboard">
      <h2>Dashboard</h2>
      <p>Estrutura de dashboard organizada e pronta para evolução.</p>
      <app-filter-bar></app-filter-bar>
    </section>
  `,
    styles: [
        ':host { display: block; padding: 24px; }',
        '.page-dashboard { display: grid; gap: 12px; }'
    ]
})
export class DashboardPageComponent {
    constructor(public dashboardService: DashboardService) { }
}