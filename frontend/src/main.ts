// src/main.ts
import { bootstrapApplication } from '@angular/platform-browser';
import { provideRouter } from '@angular/router';
import { provideHttpClient } from '@angular/common/http';
import { provideAnimations } from '@angular/platform-browser/animations';
import { environment } from './environments/environment';
import { AppComponent } from './app/app.component';
import { routes } from './app/app.routes';

// Função para tratamento global de erros
function handleError(error: Error) {
  console.error('Erro não tratado:', error);
  // Aqui você pode adicionar lógica de logging para serviços como Sentry
}

bootstrapApplication(AppComponent, {
  providers: [
    provideRouter(routes),
    provideHttpClient(),
    provideAnimations(),
    {
      provide: 'APP_INITIALIZER',
      useFactory: () => () => {
        // Configuração inicial do aplicativo
        document.documentElement.lang = 'pt-BR';
        document.documentElement.classList.add('theme-light');
      },
      deps: []
    }
  ]
}).catch(handleError);
