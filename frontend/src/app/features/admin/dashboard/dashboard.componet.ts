import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({
    selector: 'app-dashboard-shell',
    standalone: true,
    imports: [CommonModule, RouterLink],
    template: `
    <section class="dashboard-shell">
      <h2>Dashboard</h2>
      <p>Shell inicial da organização do frontend.</p>
    </section>
  `,
    styles: [
        ':host { display: block; padding: 24px; }',
        '.dashboard-shell { display: grid; gap: 12px; }'
    ]
})
export class DashboardShellComponent { }
