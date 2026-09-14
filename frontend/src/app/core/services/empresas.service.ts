// ============================================================================
// SERVIÇO DE EMPRESAS (Responsável apenas pelas chamadas HTTP)
// ============================================================================

import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { ambiente } from '../config/ambiente';
import { 
  Empresa, EmpresaCreateDto, EmpresaUpdateDto, 
  InstanciaCreateDto, InstanciaResponseDto 
} from '../models/empresa.models';

@Injectable({ providedIn: 'root' })
export class EmpresaService {
  private readonly http = inject(HttpClient);
  private readonly BASE_URL = `${ambiente.apiUrl}/empresas`;

  listarEmpresas(): Observable<Empresa[]> {
    return this.http.get<Empresa[]>(this.BASE_URL);
  }

  obterEmpresa(empresaId: number): Observable<Empresa> {
    return this.http.get<Empresa>(`${this.BASE_URL}/${empresaId}`);
  }

  criarEmpresa(dados: EmpresaCreateDto): Observable<Empresa> {
    return this.http.post<Empresa>(this.BASE_URL, dados);
  }

  atualizarEmpresa(empresaId: number, dados: EmpresaUpdateDto): Observable<Empresa> {
    return this.http.put<Empresa>(`${this.BASE_URL}/${empresaId}`, dados);
  }

  criarInstanciaWhatsapp(empresaId: number, dados: InstanciaCreateDto): Observable<InstanciaResponseDto> {
    return this.http.post<InstanciaResponseDto>(`${this.BASE_URL}/${empresaId}/instancia`, dados);
  }
}