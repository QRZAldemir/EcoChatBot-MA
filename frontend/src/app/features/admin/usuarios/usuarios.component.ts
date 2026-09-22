import { Component, OnInit } from '@angular/core';
import { UsuarioService } from '../../../core/services/usuario.service';
import { Usuario } from '../../../core/models/usuario.model';

@Component({
  selector: 'app-usuarios',
  templateUrl: './usuarios.component.html',
  styleUrls: ['./usuarios.component.scss']
})
export class UsuariosComponent implements OnInit {
  stats = { total: 0, departamentos: 0, canais: 0, conexoes: 1 };
  usuarios: Usuario[] = [];

  constructor(private usuarioService: UsuarioService) { }

  ngOnInit(): void {
    this.usuarioService.usuarios$.subscribe(usuarios => {
      this.usuarios = usuarios;
      this.atualizarStats();
    });
  }

  atualizarStats(): void {
    this.stats = this.usuarioService.getStats();
  }

  onUsuarioSalvo(): void {
    this.atualizarStats();
  }

  onUsuarioDeletado(): void {
    this.atualizarStats();
  }
}