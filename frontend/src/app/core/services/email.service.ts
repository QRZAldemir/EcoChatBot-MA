import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, map } from 'rxjs';
import { EmailEnviado, EmailEnviarDTO } from '../models/email.model';
import { environment } from '../../../environments/environment';

@Injectable({ providedIn: 'root' })
export class EmailService {
  private api = `${environment.apiUrl}/emails`;

  constructor(private http: HttpClient) {}

  listar(): Observable<EmailEnviado[]> {
    return this.http.get<any[]>(this.api).pipe(map(es => es.map(e => this._normalizar(e))));
  }

  enviar(dto: EmailEnviarDTO): Observable<EmailEnviado> {
    const payload = { destinatario: dto.destinatario, assunto: dto.assunto, corpo: dto.corpo, contato_id: dto.contatoId };
    return this.http.post<any>(this.api, payload).pipe(map(e => this._normalizar(e)));
  }

  deletar(id: number): Observable<void> {
    return this.http.delete<void>(`${this.api}/${id}`);
  }

  private _normalizar(raw: any): EmailEnviado {
    return {
      id: raw.id,
      contatoId: raw.contato_id ?? raw.contatoId,
      destinatario: raw.destinatario,
      assunto: raw.assunto,
      corpo: raw.corpo,
      status: raw.status,
      erroMensagem: raw.erro_mensagem ?? raw.erroMensagem,
      enviadoEm: raw.enviado_em ?? raw.enviadoEm,
      criadoEm: raw.criado_em ?? raw.criadoEm,
    };
  }
}
