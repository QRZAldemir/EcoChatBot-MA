import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Usuario } from '../../../core/models/usuario.model';
import { Departamento } from '../../../core/models/departamento.model';
import { Canal } from '../../../core/models/canal.model';
import { UsuarioService } from '../../../core/services/usuario.service';
import { DepartamentoService } from '../../../core/services/departamento.service';
import { CanalService } from '../../../core/services/canal.service';

@Component({
  selector: 'app-usuarios',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './usuarios.component.html',
  styleUrls: ['./usuarios.component.css']
})
export class UsuariosComponent implements OnInit {

  usuarios: Usuario[] = [];
  departamentos: Departamento[] = [];
  canais: Canal[] = [];

  // Agrupamento por departamento para exibição na tabela
  get usuariosPorDepto(): Map<string, Usuario[]> {
    return this.usuarioService.agruparPorDepartamento(this.usuariosFiltrados);
  }
  get deptosOrdenados(): string[] {
    return Array.from(this.usuariosPorDepto.keys()).sort();
  }

  // Filtros
  filtroNome = '';
  filtroDepartamentoId: number | null = null;
  filtroCanalId: number | null = null;
  filtroNivel = '';
  filtroStatus = '';

  // Formulário de cadastro / edição
  modo: 'novo' | 'editar' = 'novo';
  modalAberto = false;
  form: Partial<Usuario & { senha: string; senhaConfirm: string }> = {};

  alerta: { tipo: 'sucesso' | 'erro'; msg: string } | null = null;

  constructor(
    private usuarioService: UsuarioService,
    private departamentoService: DepartamentoService,
    private canalService: CanalService
  ) {}

  ngOnInit(): void {
    this.carregarDados();
  }

  carregarDados(): void {
    this.departamentoService.listar().subscribe(d => this.departamentos = d);
    this.canalService.listar().subscribe(c => this.canais = c);
    this.carregarUsuarios();
  }

  carregarUsuarios(): void {
    this.usuarioService.listar({
      nome: this.filtroNome || undefined,
      departamentoId: this.filtroDepartamentoId ?? undefined,
      canalId: this.filtroCanalId ?? undefined,
      nivel: this.filtroNivel || undefined,
      status: this.filtroStatus || undefined,
    }).subscribe(u => this.usuarios = u);
  }

  get usuariosFiltrados(): Usuario[] {
    return this.usuarios.filter(u =>
      (!this.filtroNome    || u.nome.toLowerCase().includes(this.filtroNome.toLowerCase())) &&
      (!this.filtroDepartamentoId || u.departamentoId === this.filtroDepartamentoId) &&
      (!this.filtroCanalId        || u.canalId === this.filtroCanalId) &&
      (!this.filtroNivel   || u.nivel === this.filtroNivel) &&
      (!this.filtroStatus  || u.status === this.filtroStatus)
    );
  }

  abrirNovo(): void {
    this.modo = 'novo';
    this.form = { status: 'ativo', nivel: 'atendente' };
    this.modalAberto = true;
  }

  abrirEditar(usuario: Usuario): void {
    this.modo = 'editar';
    this.form = { ...usuario };
    this.modalAberto = true;
  }

  salvar(): void {
    if (this.modo === 'novo') {
      this.usuarioService.criar(this.form).subscribe({
        next: () => { this.mostrarAlerta('sucesso', 'Usuário cadastrado com sucesso!'); this.fecharModal(); this.carregarUsuarios(); },
        error: () => this.mostrarAlerta('erro', 'Erro ao cadastrar usuário.')
      });
    } else {
      this.usuarioService.atualizar(this.form.id!, this.form).subscribe({
        next: () => { this.mostrarAlerta('sucesso', 'Usuário atualizado!'); this.fecharModal(); this.carregarUsuarios(); },
        error: () => this.mostrarAlerta('erro', 'Erro ao atualizar usuário.')
      });
    }
  }

  deletar(id: number): void {
    if (!confirm('Confirma exclusão do usuário?')) return;
    this.usuarioService.deletar(id).subscribe({
      next: () => { this.mostrarAlerta('sucesso', 'Usuário excluído.'); this.carregarUsuarios(); },
      error: () => this.mostrarAlerta('erro', 'Erro ao excluir usuário.')
    });
  }

  fecharModal(): void { this.modalAberto = false; }

  private mostrarAlerta(tipo: 'sucesso' | 'erro', msg: string): void {
    this.alerta = { tipo, msg };
    setTimeout(() => this.alerta = null, 4000);
  }
}
