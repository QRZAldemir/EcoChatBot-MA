// ==============================================================================
// ARQUIVO.....: usuarios.component.ts
// AUTOR.......: Aldemir Queiroz
// EMAIL.......: queiroz@almarcx.com.br
// PROJETO.....: EcoChatBot-MA - Sistema Multi-Tenant de Atendimento
// MÓDULO......: Componente Container de Usuarios
// VERSÃO......: 3.0.0
// CRIADO EM...: 2024-01-15
// ATUALIZADO..: 2026-09-19
// LINGUAGEM...: TypeScript 5.4+
// FRAMEWORK...: Angular 17+
// ==============================================================================
// DESCRIÇÃO...:
// Componente container (smart component) que orquestra o módulo de
// usuários: carrega dados do backend, exibe estatísticas, controla
// modal de criação/edição e delega ações aos componentes filhos.
//
// FUNCIONALIDADES:
// 1. Carregamento de usuários paginados
// 2. Carregamento de departamentos, canais, níveis e turnos
// 3. Cálculo de estatísticas
// 4. Controle de modal
// 5. Delegação de ações
//
// USADO POR:
// - src/app/modules/usuarios/usuarios.module.ts (rota raiz)
// ==============================================================================

import { Component, OnInit } from '@angular/core';
import { UsuarioService } from '../../core/services/usuario.service';
import { Usuario } from '../../core/models/usuario.model';

@Component({
  selector: 'app-usuarios',
  templateUrl: './usuarios.component.html',
  styleUrls: ['./usuarios.component.scss'],
})
export class UsuariosComponent implements OnInit {
  usuarios: Usuario[] = [];
  usuarioSelecionado: Usuario | null = null;
  modalAberto = false;
  stats = { total: 0, ativos: 0, conexoes: 0 };
  departamentos: any[] = [];
  canais: any[] = [];
  niveis: any[] = [];
  turnos: any[] = [];

  constructor(private usuarioService: UsuarioService) { }

  ngOnInit(): void {
    this.carregar();
    this.carregarEstatisticas();
  }

  carregar(): void {
    this.usuarioService.listar({ limit: 100 }).subscribe((res) => {
      this.usuarios = res.data as unknown as Usuario[];
      this.stats.conexoes = new Set(
        (res.data as any).flatMap((u: any) =>
          (u.conexoes || []).map((c: any) => c.id),
        ),
      ).size;
    });
  }

  carregarEstatisticas(): void {
    this.usuarioService.estatisticas().subscribe((e) => {
      this.stats.total = e.total;
      this.stats.ativos = e.ativos;
    });
  }

  abrirNovo(): void {
    this.usuarioSelecionado = null;
    this.modalAberto = true;
  }

  abrirEditar(u: Usuario): void {
    this.usuarioSelecionado = u;
    this.modalAberto = true;
  }

  fecharModal(): void {
    this.modalAberto = false;
    this.usuarioSelecionado = null;
  }

  onSalvo(): void {
    this.fecharModal();
    this.carregar();
    this.carregarEstatisticas();
  }

  onDeletar(id: number): void {
    if (!confirm('Confirma exclusão?')) return;

    this.usuarioService.deletar(id).subscribe(() => {
      this.carregar();
      this.carregarEstatisticas();
    });
  }
}