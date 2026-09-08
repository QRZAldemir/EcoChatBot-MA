import { CommonModule } from '@angular/common';
import { Component, Input } from '@angular/core';

@Component({
    selector: 'app-chart-container',
    standalone: true,
    imports: [CommonModule],
    template: `
    <div class="chart-card">
      <h4>{{ title }}</h4>
      <div class="chart-body">
        <ng-content></ng-content>
      </div>
    </div>
  `,
    styles: [
        ':host { display: block; }',
        '.chart-card { background: #fff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 16px; }',
        'h4 { margin: 0 0 12px; font-size: 1rem; }',
        '.chart-body { min-height: 180px; display: flex; align-items: center; justify-content: center; color: #6b7280; }'
    ]
})
export class ChartContainerComponent {
    @Input() title = 'Gráfico';
}
