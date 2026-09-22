import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';

@Component({
    selector: 'app-upload-feature',
    standalone: true,
    imports: [CommonModule],
    template: `
    <section>
      <h2>Upload</h2>
      <p>Feature de upload do projeto.</p>
    </section>
  `,
    styles: ['section { padding: 24px; }']
})
export class UploadComponent { }
