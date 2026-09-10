import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-topbar',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './topbar.component.html',
  styleUrls: ['./topbar.component.css']
})
export class TopbarComponent {
  @Input() usuario: { nome: string } | null = null;
  @Output() toggleMenu = new EventEmitter<void>();
  @Output() sairClick = new EventEmitter<void>();

  onToggle(): void {
    this.toggleMenu.emit();
  }

  onSair(): void {
    this.sairClick.emit();
  }
}
