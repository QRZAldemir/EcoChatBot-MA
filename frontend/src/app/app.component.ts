import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet],
  template: `<router-outlet></router-outlet>`,
  styles: [`
    :host { display: block; height: 100vh; }
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: 'Roboto', system-ui, sans-serif; }
  `]
})
export class AppComponent {}
