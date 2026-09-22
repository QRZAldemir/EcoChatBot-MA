import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { Canal } from '../../../../core/models/canal.model';
import { CanalService } from '../../../../core/services/canal.service';
import { trackById } from '../../../../core/utils/track-by';

@Component({
  selector: 'app-hub-menu',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './hub-menu.component.html',
  styleUrls: ['./hub-menu.component.css']
})
export class HubMenuComponent implements OnInit {
  readonly trackById = trackById;

  canais: Canal[] = [];

  // O cliente clica numa opção → não digita
  opcaoSelecionada: Canal | null = null;

  constructor(
    private canalService: CanalService,
    private router: Router
  ) { }

  ngOnInit(): void {
    this.canalService.listar().subscribe(c => this.canais = c.filter(x => x.ativo));
  }

  selecionarCanal(canal: Canal): void {
    // Navega para o componente de atendimento passando o canal como parâmetro
    this.router.navigate(['/chat', canal.nome.toLowerCase()], {
      state: { canal }
    });
  }
}
