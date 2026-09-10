// OnInit é uma interface de ciclo de vida (Lifecycle hook) do Angular.
import { Component, OnInit } from '@angular/core';
// Módulos nativos do Angular para usar diretivas comuns (como *ngIf, *ngFor) e formulários (ngModel).
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Canal, CANAIS_PADRAO } from '../../../core/models/canal.model';
import { CanalService } from '../../../core/services/canal.service';
import { trackById } from '../../../core/utils/track-by';

// O decorador @Component diz ao Angular que esta classe é um componente visual (UI).
@Component({
  // O 'selector' é a tag HTML personalizada gerada. Ex: <app-canais></app-canais>
  selector: 'app-canais',
  // standalone: true significa que este componente não depende de um arquivo module (ex: app.module.ts). Ele é autossuficiente.
  standalone: true,
  // Importações diretas que este componente precisará usar no seu HTML.
  imports: [CommonModule, FormsModule],
  templateUrl: './canais.component.html',
  styleUrls: ['./canais.component.css']
})
// 'implements OnInit' obriga a classe a ter o método ngOnInit().
export class CanaisComponent implements OnInit {

  readonly trackById = trackById;

  canais: Canal[] = [];
  modalAberto = false;
  modo: 'novo' | 'editar' = 'novo';
  form: Partial<Canal> = {};
  alerta: { tipo: 'sucesso' | 'erro'; msg: string } | null = null;

  // Arquivos de menu disponíveis no sistema
  arquivosMenu = [
    { arquivo: '1atendimento-ma.html', label: '📞 Atendimento ao Cliente' },
    { arquivo: '2agendamento-ma.html', label: '📅 Agendamento Ambulatório' },
    { arquivo: '3examesdiagnostico-ma.html', label: '🩺 Exames Diagnóstico' },
    { arquivo: '7portaria-ma.html', label: '🚪 Portaria' },
    { arquivo: '8ouvidoria-ma.html', label: '📢 Ouvidoria' },
  ];

  constructor(private canalService: CanalService) { }

  // ngOnInit roda automaticamente assim que o componente termina de carregar na tela.
  // O método .subscribe() "ouve" o retorno assíncrono (Observable) do backend e popula a variável canais.
  ngOnInit(): void {
    this.carregar();
  }

  carregar(): void {
    this.canalService.listar().subscribe(c => this.canais = c);
  }

  abrirNovo(): void {
    this.modo = 'novo';
    this.form = { ativo: true };
    this.modalAberto = true;
  }

  abrirEditar(canal: Canal): void {
    this.modo = 'editar';
    this.form = { ...canal };
    this.modalAberto = true;
  }

  salvar(): void {
    const op = this.modo === 'novo'
      ? this.canalService.criar(this.form)
      : this.canalService.atualizar(this.form.id!, this.form);

    op.subscribe({
      next: () => { this.mostrarAlerta('sucesso', 'Canal salvo com sucesso!'); this.fecharModal(); this.carregar(); },
      error: () => this.mostrarAlerta('erro', 'Erro ao salvar canal.')
    });
  }

  deletar(id: number): void {
    if (!confirm('Excluir este canal?')) return;
    this.canalService.deletar(id).subscribe({
      next: () => { this.mostrarAlerta('sucesso', 'Canal excluído.'); this.carregar(); },
      error: () => this.mostrarAlerta('erro', 'Erro ao excluir.')
    });
  }

  visualizarMenu(canal: Canal): void {
    const url = canal.arquivoMenu || canal.arquivo_menu || '';
    if (!url) return;
    window.open(`/assets/menus/${url}`, '_blank');
  }

  fecharModal(): void { this.modalAberto = false; }

  private mostrarAlerta(tipo: 'sucesso' | 'erro', msg: string): void {
    this.alerta = { tipo, msg };
    setTimeout(() => this.alerta = null, 4000);
  }
}
