import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Departamento } from '../../../core/models/departamento.model';
import { DepartamentoService } from '../../../core/services/departamento.service';

@Component({
  selector: 'app-departamentos',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './departamentos.component.html',
  styleUrls: ['./departamentos.component.css']
})
export class DepartamentosComponent implements OnInit {

  departamentos: Departamento[] = [];
  modalAberto = false;
  modo: 'novo' | 'editar' = 'novo';
  form: Partial<Departamento> = {};
  alerta: { tipo: 'sucesso' | 'erro'; msg: string } | null = null;

  constructor(private departamentoService: DepartamentoService) {}

  ngOnInit(): void {
    this.departamentoService.listar().subscribe(d => this.departamentos = d);
  }

  abrirNovo(): void {
    this.modo = 'novo';
    this.form = { ativo: true };
    this.modalAberto = true;
  }

  abrirEditar(d: Departamento): void {
    this.modo = 'editar';
    this.form = { ...d };
    this.modalAberto = true;
  }

  salvar(): void {
    const op = this.modo === 'novo'
      ? this.departamentoService.criar(this.form)
      : this.departamentoService.atualizar(this.form.id!, this.form);

    op.subscribe({
      next: () => { this.mostrarAlerta('sucesso', 'Departamento salvo!'); this.fecharModal(); this.ngOnInit(); },
      error: () => this.mostrarAlerta('erro', 'Erro ao salvar.')
    });
  }

  deletar(id: number): void {
    if (!confirm('Excluir departamento?')) return;
    this.departamentoService.deletar(id).subscribe({
      next: () => { this.mostrarAlerta('sucesso', 'Departamento excluído.'); this.ngOnInit(); },
      error: () => this.mostrarAlerta('erro', 'Erro ao excluir.')
    });
  }

  fecharModal(): void { this.modalAberto = false; }

  private mostrarAlerta(tipo: 'sucesso' | 'erro', msg: string): void {
    this.alerta = { tipo, msg };
    setTimeout(() => this.alerta = null, 4000);
  }
}
