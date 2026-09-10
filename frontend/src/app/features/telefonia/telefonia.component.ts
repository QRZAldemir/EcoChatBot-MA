import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';

@Component({
    selector: 'app-telefonia-feature',
    standalone: true,
    imports: [CommonModule],
    template: `
    <section>
      <h2>Telefonia</h2>
      <p>Feature de telefonia do projeto.</p>
    </section>
  `,
    styles: ['section { padding: 24px; }']
})
export class TelefoniaComponent { }
