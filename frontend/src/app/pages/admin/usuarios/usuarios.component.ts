import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Usuario } from '../../../core/models/usuario.model';
import { Departamento } from '../../../core/models/departamento.model';
import { Canal } from '../../../core/models/canal.model';
import { UsuarioService } from '../../../core/services/usuario.service';
import { DepartamentoService } from '../../../core/services/departamento.service';
import { CanalService } from '../../../core/services/canal.service';
import { CanalByIdPipe } from '../../../core/pipes/canal-by-id.pipe';
import { trackById } from '../../../core/utils/track-by';

@Component({
  selector: 'app-usuarios',
  standalone: true,
  imports: [CommonModule, FormsModule, CanalByIdPipe],
  templateUrl: './usuarios.component.html',
  styleUrls: ['./usuarios.component.css']
})
export class UsuariosComponent implements OnInit {

  usuarios: Usuario[] = [];
  departamentos: Departamento[] = [];
  canais: Canal[] = [];

  // Agrupamento por departamento, calculado uma única vez a cada carga (não a
  // cada change detection): usuariosPorDepto/deptosOrdenados eram getters que
  // recriavam um Map e um array novos a cada ciclo, mesmo sem os dados mudarem.
  usuariosPorDepto = new Map<string, Usuario[]>();
  deptosOrdenados: string[] = [];

  readonly trackById = trackById;

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
  ) { }

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
    }).subscribe(u => this._aplicarUsuarios(u));
  }

  // O backend já aplica os filtros (ver carregarUsuarios); aqui só cacheamos
  // o agrupamento por departamento como referência estável até a próxima carga.
  private _aplicarUsuarios(usuarios: Usuario[]): void {
    this.usuarios = usuarios;
    this.usuariosPorDepto = this.usuarioService.agruparPorDepartamento(usuarios);
    this.deptosOrdenados = Array.from(this.usuariosPorDepto.keys()).sort();
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
