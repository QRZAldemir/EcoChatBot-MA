import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-escalas',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="panel">
      <div class="panel-header">
        <div class="panel-icon teal"><i class="fas fa-calendar-alt"></i></div>
        <h3>Painel de Escalas</h3>
      </div>
      <div class="pb" style="padding:40px;text-align:center;color:#78716c">
        <i class="fas fa-calendar-alt" style="font-size:48px;margin-bottom:16px;display:block;opacity:0.3"></i>
        <p>O painel de escalas será exibido aqui após integração com o módulo de RH.</p>
      </div>
    </div>
  `
})
export class EscalasComponent {}
