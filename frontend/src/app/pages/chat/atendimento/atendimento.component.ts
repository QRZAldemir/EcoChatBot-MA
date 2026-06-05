import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';
import { CanalService } from '../../../core/services/canal.service';
import { Canal } from '../../../core/models/canal.model';

@Component({
  selector: 'app-atendimento',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './atendimento.component.html',
  styleUrls: ['./atendimento.component.css']
})
export class AtendimentoComponent implements OnInit {

  canal: Canal | null = null;
  iframeUrl: SafeResourceUrl | null = null;
  carregando = true;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private sanitizer: DomSanitizer,
    private canalService: CanalService
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

  private carregarCanal(canal: Canal): void {
    this.canal = canal;
    // Os HTMLs ficam em /assets/menus/ (copiados do protótipo)
    const url = `/assets/menus/${canal.arquivoMenu}`;
    this.iframeUrl = this.sanitizer.bypassSecurityTrustResourceUrl(url);
    this.carregando = false;
  }

  voltar(): void {
    this.router.navigate(['/chat/menu']);
  }
}
