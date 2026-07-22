import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { CanalService } from '../../../core/services/canal.service';
import { MenuService } from '../../../core/services/menu.service';
import { ModeloMensagemService } from '../../../core/services/modelo-mensagem.service';
import { Canal } from '../../../core/models/canal.model';
import { Menu, MenuOpcao } from '../../../core/models/menu.model';
import { ModeloMensagem } from '../../../core/models/modelo-mensagem.model';

const MODELO_CORES = ['yellow', 'pink', 'blue', 'green', 'purple', 'orange', 'teal', 'red'];

@Component({
  selector: 'app-atendimento',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './atendimento.component.html',
  styleUrls: ['./atendimento.component.css']
})
export class AtendimentoComponent implements OnInit {

  canal: Canal | null = null;
  menu: Menu | null = null;
  opcaoSelecionada: MenuOpcao | null = null;
  carregando = true;

  // ── Mensagens prontas ──
  mensagensModalAberto = false;
  carregandoMensagens = false;
  modelos: ModeloMensagem[] = [];
  buscaMensagem = '';
  mensagemExpandida: ModeloMensagem | null = null;
  copiadoId: number | null = null;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private canalService: CanalService,
    private menuService: MenuService,
    private modeloMensagemService: ModeloMensagemService,
  ) {}

  ngOnInit(): void {
    // Tenta pegar o canal passado via router state (quando vem do hub-menu)
    const state = history.state as { canal?: Canal };

    if (state?.canal) {
      this.carregarCanal(state.canal);
    } else {
      // Fallback: busca o canal pelo nome na URL (/chat/portaria → busca "Portaria")
      const nomeRota = this.route.snapshot.paramMap.get('canal') ?? '';
      this.canalService.listar().subscribe(canais => {
        const encontrado = canais.find(c =>
          c.nome.toLowerCase().replace(/[^a-z0-9]/g, '') === nomeRota.toLowerCase().replace(/[^a-z0-9]/g, '')
        );
        if (encontrado) {
          this.carregarCanal(encontrado);
        } else {
          this.router.navigate(['/chat/menu']);
        }
      });
    }
  }

  // rowId é estável e sempre presente (id só existe depois de salvo no backend).
  trackByOpcao(_indice: number, opcao: MenuOpcao): string {
    return opcao.rowId;
  }

  selecionarOpcao(opcao: MenuOpcao): void {
    this.opcaoSelecionada = this.opcaoSelecionada?.rowId === opcao.rowId ? null : opcao;
  }

  private carregarCanal(canal: Canal): void {
    this.canal = canal;
    this.opcaoSelecionada = null;

    // A mensagem interativa do canal é cadastrada em Configuração → Mensagens
    // (tela "Mensagem Interativa"), não mais um HTML estático em assets/menus.
    this.menuService.listar(canal.id, true).subscribe({
      next: menus => {
        this.menu = menus[0] ?? null;
        this.carregando = false;
      },
      error: () => {
        this.menu = null;
        this.carregando = false;
      },
    });
  }

  voltar(): void {
    this.router.navigate(['/chat/menu']);
  }

  // ── Mensagens prontas ──

  trackByModelo(_indice: number, modelo: ModeloMensagem): number {
    return modelo.id;
  }

  corModelo(modelo: ModeloMensagem): string {
    return MODELO_CORES[modelo.id % MODELO_CORES.length];
  }

  get modelosFiltrados(): ModeloMensagem[] {
    const termo = this.buscaMensagem.trim().toLowerCase();
    const ativos = this.modelos.filter(m => m.ativo);
    if (!termo) return ativos;
    return ativos.filter(m =>
      m.descricao.toLowerCase().includes(termo) ||
      m.corpo.toLowerCase().includes(termo)
    );
  }

  abrirMensagensProntas(): void {
    this.mensagensModalAberto = true;
    if (this.modelos.length === 0) {
      this.carregandoMensagens = true;
      this.modeloMensagemService.listar().subscribe({
        next: modelos => { this.modelos = modelos; this.carregandoMensagens = false; },
        error: () => { this.carregandoMensagens = false; },
      });
    }
  }

  fecharMensagensProntas(): void {
    this.mensagensModalAberto = false;
    this.buscaMensagem = '';
    this.mensagemExpandida = null;
  }

  expandirMensagem(modelo: ModeloMensagem): void {
    this.mensagemExpandida = modelo;
  }

  fecharMensagemExpandida(): void {
    this.mensagemExpandida = null;
  }

  copiarMensagem(modelo: ModeloMensagem): void {
    navigator.clipboard.writeText(modelo.corpo).then(() => {
      this.copiadoId = modelo.id;
      setTimeout(() => { this.copiadoId = null; }, 1500);
    });
  }
}
