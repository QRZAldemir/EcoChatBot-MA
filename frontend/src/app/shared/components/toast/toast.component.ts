import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';

@Component({
    selector: 'app-toast',
    standalone: true,
    imports: [CommonModule],
    template: `
    <div class="toast" *ngIf="message">
      {{ message }}
    </div>
  `,
    styles: [
        ':host { position: fixed; right: 20px; bottom: 20px; z-index: 9999; }',
        '.toast { background: #111827; color: white; padding: 12px 16px; border-radius: 8px; box-shadow: 0 10px 25px rgba(0,0,0,.16); }'
    ]
})
export class ToastComponent implements OnInit {
    message = '';

    ngOnInit(): void {
        document.addEventListener('showToast', ((event: Event) => {
            const custom = event as CustomEvent<{ message: string }>;
            this.message = custom.detail?.message || '';
            if (this.message) {
                setTimeout(() => this.message = '', 2500);
            }
        }) as EventListener);
    }
}
