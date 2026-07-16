import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { Observable, forkJoin } from 'rxjs';

import { ModeloMensagem } from '../../../core/models/modelo-mensagem.model';
import { Menu, MenuOpcao } from '../../../core/models/menu.model';
import { Departamento } from '../../../core/models/departamento.model';
import { Canal } from '../../../core/models/canal.model';
import { ModeloMensagemService } from '../../../core/services/modelo-mensagem.service';
import { MenuService } from '../../../core/services/menu.service';
import { DepartamentoService } from '../../../core/services/departamento.service';
import { CanalService } from '../../../core/services/canal.service';
import { environment } from '../../../../environments/environment';

type TipoMensagem = 'Padrão' | 'Interativa';

interface MensagemRow {
  id: number;
  tipo: TipoMensagem;
  descricao: string;
  donoNome: string;
  raw: ModeloMensagem | Menu;
}

@Component({
  selector: 'app-mensagens',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './mensagens.component.html',
  styleUrls: ['./mensagens.component.css']
})
export class MensagensComponent implements OnInit {

  linhas: MensagemRow[] = [];
  departamentos: Departamento[] = [];
  canais: Canal[] = [];

  filtroDescricao = '';
  filtroTipo: 'Todos' | TipoMensagem = 'Todos';

  modalTipoAberto = false;
  view: 'lista' | 'padrao' | 'interativa' = 'lista';
  modo: 'novo' | 'editar' = 'novo';

  formPadrao: Partial<ModeloMensagem> = {};
  gerandoAudio = false;

  formInterativa: Partial<Menu> = {};
  opcoesRemovidas: number[] = [];
  novaOpcao: Partial<MenuOpcao> = { titulo: '', rowId: '' };
  destinoCanalId: number | null = null;

  alerta: { tipo: 'sucesso' | 'erro'; msg: string } | null = null;

  constructor(
    private modeloService: ModeloMensagemService,
    private menuService: MenuService,
    private departamentoService: DepartamentoService,
    private canalService: CanalService,
    private http: HttpClient,
  ) {}

  ngOnInit(): void {
    this.departamentoService.listar().subscribe(d => this.departamentos = d);
    this.canalService.listar().subscribe(c => { this.canais = c; this.carregar(); });
  }

  carregar(): void {
    forkJoin([this.modeloService.listar(), this.menuService.listar()]).subscribe(([modelos, menus]) => {
      const linhasPadrao: MensagemRow[] = modelos.map(m => ({
        id: m.id, tipo: 'Padrão', descricao: m.descricao,
        donoNome: m.departamentoNome || '—', raw: m,
      }));
      const linhasInterativa: MensagemRow[] = menus.map(m => ({
        id: m.id, tipo: 'Interativa', descricao: m.titulo,
        donoNome: this.nomeDestino(m.canalId), raw: m,
      }));
      this.linhas = [...linhasPadrao, ...linhasInterativa];
    });
  }

  nomeDestino(canalId?: number): string {
    if (!canalId) return '🏠 Menu Principal';
    const canal = this.canais.find(c => c.id === canalId);
    return canal ? (canal.departamentoNome || canal.nome) : '—';
  }

  get linhasFiltradas(): MensagemRow[] {
    const busca = this.filtroDescricao.trim().toLowerCase();
    return this.linhas.filter(l =>
      (this.filtroTipo === 'Todos' || l.tipo === this.filtroTipo) &&
      (!busca || l.descricao.toLowerCase().includes(busca))
    );
  }

  // ── Navegação entre lista / formulários ──────────────────────

  abrirNovo(): void { this.modalTipoAberto = true; }

  escolherTipo(tipo: TipoMensagem): void {
    this.modalTipoAberto = false;
    this.modo = 'novo';
    if (tipo === 'Padrão') {
      this.formPadrao = { ativo: true };
      this.view = 'padrao';
    } else {
      this.formInterativa = { ativo: true, textoBotao: 'Ver opções', opcoes: [] };
      this.destinoCanalId = null;
      this.opcoesRemovidas = [];
      this.view = 'interativa';
    }
  }

  editar(linha: MensagemRow): void {
    this.modo = 'editar';
    if (linha.tipo === 'Padrão') {
      this.formPadrao = { ...(linha.raw as ModeloMensagem) };
      this.view = 'padrao';
    } else {
      const menu = linha.raw as Menu;
      this.formInterativa = { ...menu, opcoes: menu.opcoes.map(o => ({ ...o })) };
      this.opcoesRemovidas = [];
      this.destinoCanalId = null;
      this.view = 'interativa';
    }
  }

  excluir(linha: MensagemRow): void {
    if (!confirm(`Excluir a mensagem "${linha.descricao}"?`)) return;
    const op = linha.tipo === 'Padrão' ? this.modeloService.deletar(linha.id) : this.menuService.deletar(linha.id);
    op.subscribe({
      next: () => { this.mostrarAlerta('sucesso', 'Mensagem excluída.'); this.carregar(); },
      error: () => this.mostrarAlerta('erro', 'Erro ao excluir mensagem.'),
    });
  }

  voltar(): void { this.view = 'lista'; }

  // ── Mensagem Padrão ───────────────────────────────────────────

  gerarAudio(): void {
    const texto = (this.formPadrao.corpo || '').trim();
    if (!texto) { this.mostrarAlerta('erro', 'Digite o texto da mensagem antes de gerar o áudio.'); return; }

    this.gerandoAudio = true;
    this.http.post<{ sucesso: boolean; url: string }>(`${environment.apiUrl}/audio/gerar`, { texto })
      .subscribe({
        next: (res) => {
          this.formPadrao.arquivo = res.url;
          this.gerandoAudio = false;
        },
        error: () => {
          this.gerandoAudio = false;
          this.mostrarAlerta('erro', 'Erro ao gerar áudio.');
        },
      });
  }

  removerArquivo(): void {
    this.formPadrao.arquivo = undefined;
  }

  salvarPadrao(): void {
    if (!this.formPadrao.descricao?.trim() || !this.formPadrao.corpo?.trim()) {
      this.mostrarAlerta('erro', 'Descrição e Mensagem são obrigatórias.');
      return;
    }
    const op = this.modo === 'novo'
      ? this.modeloService.criar(this.formPadrao)
      : this.modeloService.atualizar(this.formPadrao.id!, this.formPadrao);

    op.subscribe({
      next: () => { this.mostrarAlerta('sucesso', 'Mensagem salva!'); this.view = 'lista'; this.carregar(); },
      error: () => this.mostrarAlerta('erro', 'Erro ao salvar mensagem.'),
    });
  }

  // ── Mensagem Interativa ───────────────────────────────────────

  get ehHub(): boolean {
    return !this.formInterativa.canalId;
  }

  onDestinoCanalChange(): void {
    if (!this.destinoCanalId) return;
    const canal = this.canais.find(c => c.id === this.destinoCanalId);
    if (!canal) return;
    this.novaOpcao.rowId = `CANAL_${canal.id}`;
    if (!this.novaOpcao.titulo) this.novaOpcao.titulo = canal.departamentoNome || canal.nome;
  }

  adicionarOpcao(): void {
    const opcoes = this.formInterativa.opcoes ?? [];
    if (opcoes.length >= 3) { this.mostrarAlerta('erro', 'Máximo de 3 opções por mensagem.'); return; }
    if (!this.novaOpcao.titulo?.trim() || !this.novaOpcao.rowId?.trim()) {
      this.mostrarAlerta('erro', 'Preencha Título e Identificador da opção.');
      return;
    }
    this.formInterativa.opcoes = [
      ...opcoes,
      { titulo: this.novaOpcao.titulo, rowId: this.novaOpcao.rowId, descricao: this.novaOpcao.descricao, ordem: opcoes.length } as MenuOpcao,
    ];
    this.novaOpcao = { titulo: '', rowId: '' };
    this.destinoCanalId = null;
  }

  removerOpcao(indice: number): void {
    const opcoes = [...(this.formInterativa.opcoes ?? [])];
    const [removida] = opcoes.splice(indice, 1);
    if (removida?.id) this.opcoesRemovidas.push(removida.id);
    this.formInterativa.opcoes = opcoes;
  }

  salvarInterativa(): void {
    if (!this.formInterativa.titulo?.trim() || !this.formInterativa.descricao?.trim()) {
      this.mostrarAlerta('erro', 'Descrição e Corpo são obrigatórios.');
      return;
    }
    if (!this.formInterativa.opcoes?.length) {
      this.mostrarAlerta('erro', 'Adicione ao menos uma opção.');
      return;
    }

    if (this.modo === 'novo') {
      this.menuService.criar(this.formInterativa).subscribe({
        next: () => { this.mostrarAlerta('sucesso', 'Mensagem interativa salva!'); this.view = 'lista'; this.carregar(); },
        error: () => this.mostrarAlerta('erro', 'Erro ao salvar mensagem interativa.'),
      });
      return;
    }

    const menuId = this.formInterativa.id!;
    const chamadas: Observable<unknown>[] = [this.menuService.atualizar(menuId, this.formInterativa)];
    for (const id of this.opcoesRemovidas) chamadas.push(this.menuService.deletarOpcao(id));
    (this.formInterativa.opcoes ?? []).forEach((opcao, indice) => {
      const payload = { ...opcao, ordem: indice };
      chamadas.push(opcao.id ? this.menuService.atualizarOpcao(opcao.id, payload) : this.menuService.adicionarOpcao(menuId, payload));
    });

    forkJoin(chamadas).subscribe({
      next: () => { this.mostrarAlerta('sucesso', 'Mensagem interativa salva!'); this.view = 'lista'; this.carregar(); },
      error: () => this.mostrarAlerta('erro', 'Erro ao salvar mensagem interativa.'),
    });
  }

  private mostrarAlerta(tipo: 'sucesso' | 'erro', msg: string): void {
    this.alerta = { tipo, msg };
    setTimeout(() => this.alerta = null, 4000);
  }
}
