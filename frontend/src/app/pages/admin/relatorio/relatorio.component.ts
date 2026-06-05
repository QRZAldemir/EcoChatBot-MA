import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-relatorio',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="panel">
      <div class="panel-header">
        <div class="panel-icon blue"><i class="fas fa-chart-bar"></i></div>
        <h3>Relatórios</h3>
      </div>
      <div class="pb" style="padding:40px;text-align:center;color:#78716c">
        <i class="fas fa-chart-bar" style="font-size:48px;margin-bottom:16px;display:block;opacity:0.3"></i>
        <p>Relatórios serão exibidos aqui conforme os dados de atendimento forem registrados.</p>
      </div>
    </div>
  `
})
export class RelatorioComponent {}
