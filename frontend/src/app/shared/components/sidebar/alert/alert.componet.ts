import { Component, Input, OnDestroy } from '@angular/core';

export type AlertType = 'ok' | 'err';

@Component({
  selector: 'app-alert',
  templateUrl: './alert.component.html',
  styleUrls: ['./alert.component.scss']
})
export class AlertComponent implements OnDestroy {
  @Input() type: AlertType = 'ok';
  @Input() message: string = '';
  @Input() duration: number = 4000;

  private timeoutId: any;

  ngOnDestroy(): void {
    if (this.timeoutId) {
      clearTimeout(this.timeoutId);
    }
  }

  close(): void {
    if (this.timeoutId) {
      clearTimeout(this.timeoutId);
    }
    // Emitir evento ou remover componente
  }

  scheduleClose(): void {
    this.timeoutId = setTimeout(() => {
      this.close();
    }, this.duration);
  }
}