import { Component } from '@angular/core';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';

@Component({
  selector: 'app-escalas',
  standalone: true,
  template: `
    <div style="height:calc(100vh - 92px)">
      <iframe [src]="url" style="width:100%;height:100%;border:none;border-radius:10px" title="Painel de Escalas"></iframe>
    </div>
  `
})
export class EscalasComponent {
  url: SafeResourceUrl;
  constructor(s: DomSanitizer) {
    this.url = s.bypassSecurityTrustResourceUrl('/assets/menus/../../../Painel_Escalas_Mackenzie.html');
  }
}
