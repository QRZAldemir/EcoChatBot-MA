import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface MensagemIA {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

export interface RespostaIA {
  resposta: string;
  tokens?: number;
}

@Injectable({ providedIn: 'root' })
export class DeepSeekService {
  private api = `${environment.apiUrl}/ia`;

  constructor(private http: HttpClient) {}

  // Envia histórico de conversa e retorna resposta do DeepSeek
  conversar(mensagens: MensagemIA[], canal: string): Observable<RespostaIA> {
    return this.http.post<RespostaIA>(`${this.api}/conversar`, { mensagens, canal });
  }

  // Gera resposta para opção selecionada pelo cliente no menu
  responderOpcao(opcao: string, canal: string, contexto?: string): Observable<RespostaIA> {
    return this.http.post<RespostaIA>(`${this.api}/opcao`, { opcao, canal, contexto });
  }
}
