import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { trackById } from '../../core/utils/track-by';

interface NivelUI {
  id: number;
  codigo: string;
  nome: string;
  descricao: string;
  permissoes: { modulo: string; leitura: boolean; escrita: boolean; exclusao: boolean }[];
}

@Component({
  selector: 'app-niveis',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './niveis.component.html',
  styleUrls: ['./niveis.component.css']
})
export class NiveisComponent {
  readonly trackById = trackById;

  niveis: NivelUI[] = [
    {
      id: 1, codigo: 'atendente', nome: 'Atendente',
      descricao: 'Acesso ao chat e atendimento do canal vinculado',
      permissoes: [
        { modulo: 'Chat',          leitura: true,  escrita: true,  exclusao: false },
        { modulo: 'Usuários',      leitura: false, escrita: false, exclusao: false },
        { modulo: 'Canais',        leitura: false, escrita: false, exclusao: false },
        { modulo: 'Relatórios',    leitura: false, escrita: false, exclusao: false },
      ]
    },
    {
      id: 2, codigo: 'supervisor', nome: 'Supervisor',
      descricao: 'Monitora atendimentos e equipe do departamento',
      permissoes: [
        { modulo: 'Chat',          leitura: true,  escrita: true,  exclusao: true  },
        { modulo: 'Usuários',      leitura: true,  escrita: false, exclusao: false },
        { modulo: 'Canais',        leitura: true,  escrita: false, exclusao: false },
        { modulo: 'Relatórios',    leitura: true,  escrita: false, exclusao: false },
      ]
    },
    {
      id: 3, codigo: 'gerente', nome: 'Gerente',
      descricao: 'Gerencia usuários e configurações do departamento',
      permissoes: [
        { modulo: 'Chat',          leitura: true,  escrita: true,  exclusao: true  },
        { modulo: 'Usuários',      leitura: true,  escrita: true,  exclusao: false },
        { modulo: 'Canais',        leitura: true,  escrita: true,  exclusao: false },
        { modulo: 'Relatórios',    leitura: true,  escrita: true,  exclusao: false },
      ]
    },
    {
      id: 4, codigo: 'administrador', nome: 'Administrador',
      descricao: 'Acesso total ao sistema',
      permissoes: [
        { modulo: 'Chat',          leitura: true,  escrita: true,  exclusao: true  },
        { modulo: 'Usuários',      leitura: true,  escrita: true,  exclusao: true  },
        { modulo: 'Canais',        leitura: true,  escrita: true,  exclusao: true  },
        { modulo: 'Relatórios',    leitura: true,  escrita: true,  exclusao: true  },
      ]
    },
  ];

  nivelSelecionado: NivelUI | null = null;

  selecionar(n: NivelUI): void {
    this.nivelSelecionado = this.nivelSelecionado?.id === n.id ? null : n;
  }
}
