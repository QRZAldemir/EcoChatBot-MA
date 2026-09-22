import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';

@Component({
    selector: 'app-avaliacao-feature',
    standalone: true,
    imports: [CommonModule],
    template: `
    <section>
      <h2>Avaliação</h2>
      <p>Feature de avaliação do projeto.</p>
    </section>
  `,
    styles: ['section { padding: 24px; }']
})
export class AvaliacaoComponent { }
