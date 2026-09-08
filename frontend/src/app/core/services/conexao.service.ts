import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, map } from 'rxjs';
import { Conexao, ConexaoQRCode } from '../models/conexao.model';
import { environment } from '../../../environments/environment';

@Injectable({ providedIn: 'root' })
export class ConexaoService {
  private api = `${environment.apiUrl}/conexoes`;

  constructor(private http: HttpClient) { }

  listar(): Observable<Conexao[]> {
    return this.http.get<any[]>(this.api).pipe(map(cs => cs.map(c => this._normalizar(c))));
  }

  criar(dto: Partial<Conexao>): Observable<ConexaoQRCode> {
    return this.http.post<any>(this.api, this._serializar(dto)).pipe(map(r => this._normalizarQr(r)));
  }

  atualizar(id: number, dto: Partial<Conexao>): Observable<Conexao> {
    return this.http.put<any>(`${this.api}/${id}`, this._serializar(dto)).pipe(map(c => this._normalizar(c)));
  }

  deletar(id: number): Observable<void> {
    return this.http.delete<void>(`${this.api}/${id}`);
  }

  atualizarStatus(id: number): Observable<Conexao> {
    return this.http.post<any>(`${this.api}/${id}/atualizar`, {}).pipe(map(c => this._normalizar(c)));
  }

  desconectar(id: number): Observable<Conexao> {
    return this.http.post<any>(`${this.api}/${id}/desconectar`, {}).pipe(map(c => this._normalizar(c)));
  }

  reconectar(id: number): Observable<ConexaoQRCode> {
    return this.http.post<any>(`${this.api}/${id}/reconectar`, {}).pipe(map(r => this._normalizarQr(r)));
  }

  limparFila(id: number): Observable<Conexao> {
    return this.http.post<any>(`${this.api}/${id}/limpar-fila`, {}).pipe(map(c => this._normalizar(c)));
  }

  tornarPadrao(id: number): Observable<Conexao> {
    return this.http.post<any>(`${this.api}/${id}/tornar-padrao`, {}).pipe(map(c => this._normalizar(c)));
  }

  alternarAtivo(id: number): Observable<Conexao> {
    return this.http.post<any>(`${this.api}/${id}/alternar-ativo`, {}).pipe(map(c => this._normalizar(c)));
  }

  private _normalizar(raw: any): Conexao {
    return {
      id: raw.id,
      nome: raw.nome,
      telefone: raw.telefone,
      tipo: raw.tipo,
      conexao: raw.conexao,
      atendimento: raw.atendimento,
      status: raw.status,
      padrao: raw.padrao,
      ativo: raw.ativo,
      criadoEm: raw.criado_em ?? raw.criadoEm,
      fila: raw.fila ?? 0,
      recebimentoMin: raw.recebimento_min ?? raw.recebimentoMin ?? 0,
    };
  }

  private _normalizarQr(raw: any): ConexaoQRCode {
    return {
      conexao: this._normalizar(raw.conexao),
      qrcodeBase64: raw.qrcode_base64 ?? raw.qrcodeBase64,
      pairingCode: raw.pairing_code ?? raw.pairingCode,
      simulado: raw.simulado,
      mensagem: raw.mensagem,
    };
  }

  private _serializar(dto: Partial<Conexao>): Record<string, unknown> {
    const { id, criadoEm, fila, recebimentoMin, status, padrao, ...rest } = dto as any;
    return rest;
  }
}
