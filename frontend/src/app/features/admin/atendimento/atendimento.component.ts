import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';

@Component({
    selector: 'app-atendimento-feature',
    standalone: true,
    imports: [CommonModule],
    template: `
    <section>
      <h2>Atendimento</h2>
      <p>Feature de atendimento do projeto.</p>
    </section>
  `,
    styles: ['section { padding: 24px; }']
})
export class AtendimentoComponent { }
