import { Component, Input, Output, EventEmitter, OnInit } from '@angular/core';
import { UsuarioService } from '../../../../../core/services/usuario.service';
import { DepartamentoService } from '../../../../../core/services/departamento.service';
import { CanalService } from '../../../../../core/services/canal.service';
import { Usuario } from '../../../../../core/models/usuario.model';
import { Departamento } from '../../../../../core/models/departamento.model';
import { Canal } from '../../../../../core/models/canal.model';

@Component({
  selector: 'app-usuario-list',
  templateUrl: './usuario-list.component.html',
  styleUrls: ['./usuario-list.component.scss']
})
export class UsuarioListComponent implements OnInit {
  @Input() usuarios: Usuario[] = [];
  @Output() usuarioDeletado = new EventEmitter<void>();

  filtroNome: string = '';
  filtroDepto: string = '';
  filtroStatus: string = '';

  departamentos: Departamento[] = [];
  canais: Canal[] = [];

  constructor(
    private usuarioService: UsuarioService,
    private deptoService: DepartamentoService,
    private canalService: CanalService
  ) { }

  ngOnInit(): void {
    this.deptoService.departamentos$.subscribe(deptos => {
      this.departamentos = deptos;
    });

    this.canalService.canais$.subscribe(canais => {
      this.canais = canais;
    });
  }

  onFiltroChange(): void {
    // Mantém o filtro na UI; os getters reativos já refletem os valores ativos.
  }

  get usuariosFiltrados(): Usuario[] {
    let filtrados = this.usuarios;

    if (this.filtroNome) {
      const nome = this.filtroNome.toLowerCase();
      filtrados = filtrados.filter(u =>
        u.nome.toLowerCase().includes(nome) ||
        u.usuario.toLowerCase().includes(nome)
      );
    }

    if (this.filtroDepto) {
      filtrados = filtrados.filter(u => u.depto === this.filtroDepto);
    }

    if (this.filtroStatus) {
      filtrados = filtrados.filter(u => u.status === this.filtroStatus);
    }

    return filtrados;
  }

  get usuariosAgrupados(): { [key: string]: Usuario[] } {
    const grupos: { [key: string]: Usuario[] } = {};
    this.usuariosFiltrados.forEach(u => {
      const key = u.depto ?? 'Sem departamento';
      if (!grupos[key]) {
        grupos[key] = [];
      }
      grupos[key].push(u);
    });
    return grupos;
  }

  getDeptoLabel(depto: string | undefined): string {
    if (!depto) return '—';
    const found = this.departamentos.find(d => d.nome === depto);
    return found ? found.nome : depto;
  }

  getCanalLabel(canal: string | undefined): string {
    if (!canal) return '—';
    const found = this.canais.find(c => c.nome === canal);
    return found ? `${found.icone} ${found.nome}` : canal;
  }

  getConexaoLabel(conexao: string | undefined): string {
    const conexoes: { [key: string]: string } = {
      '67-3416-7800': '67 3416-7800 — Oficial',
      '67-3416-7801': '67 3416-7801 — Suporte'
    };
    return conexoes[conexao || ''] || conexao || '—';
  }

  deletar(id: number): void {
    if (confirm('Confirma exclusão deste usuário?')) {
      this.usuarioService.deletarUsuario(id);
      this.usuarioDeletado.emit();
    }
  }
}