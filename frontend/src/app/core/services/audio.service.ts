import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface AudioGerado {
  sucesso: boolean;
  arquivo: string;
  url: string;
}

@Injectable({ providedIn: 'root' })
export class AudioService {
  private api = `${environment.apiUrl}/audio`;

  constructor(private http: HttpClient) {}

  gerar(texto: string): Observable<AudioGerado> {
    return this.http.post<AudioGerado>(`${this.api}/gerar`, { texto });
  }
}
