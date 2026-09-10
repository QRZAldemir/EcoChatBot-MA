// services/dashboard.service.ts
import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable, combineLatest, map } from 'rxjs';
import { Atendimento, AtendimentoStats, Avaliacao, FilterValues } from '../models/dashboard.model';
import { AtendimentoService } from './atendimento.service';
import { ArquivoService } from './arquivo.service';

@Injectable({ providedIn: 'root' })
export class DashboardService {
    private http = inject(HttpClient);
    private atendimentoService = inject(AtendimentoService);
    private arquivoService = inject(ArquivoService);

    // Estado reativo
    private atendimentosSubject = new BehaviorSubject<Atendimento[]>([]);
    atendimentos$ = this.atendimentosSubject.asObservable();

    private avaliacoesSubject = new BehaviorSubject<Avaliacao[]>([]);
    avaliacoes$ = this.avaliacoesSubject.asObservable();

    private filtrosSubject = new BehaviorSubject<FilterValues>({});
    filtros$ = this.filtrosSubject.asObservable();

    // Dados filtrados
    atendimentosFiltrados$ = combineLatest([
        this.atendimentos$,
        this.filtros$
    ]).pipe(
        map(([atendimentos, filtros]) => this.aplicarFiltros(atendimentos, filtros))
    );

    constructor() {
        this.carregarDadosIniciais();
    }

    // ─── CARREGAR DADOS ──────────────────────────────────────────

    private carregarDadosIniciais(): void {
        // Busca dados do backend via seu serviço existente
        this.atendimentoService.listar().subscribe({
            next: (dados) => {
                this.atendimentosSubject.next((dados.registros ?? []) as unknown as Atendimento[]);
            },
            error: () => {
                // Fallback para dados mock se não tiver backend
                this.carregarDadosMock();
            }
        });
    }

    private carregarDadosMock(): void {
        // Dados mock para desenvolvimento
        const mock: Atendimento[] = [
            {
                protocolo: '001',
                nome: 'João Silva',
                departamento: 'Atendimento ao Cliente',
                atendente: 'Maria Santos',
                dataCriacao: new Date(),
                status: 'finalizado',
                tipo: 'humano'
            },
            // ... mais dados
        ];
        this.atendimentosSubject.next(mock);
    }

    // ─── IMPORTAÇÃO DE ARQUIVOS ──────────────────────────────────

    importarAtendimento(file: File): Observable<Atendimento[]> {
        return new Observable(observer => {
            this.arquivoService.lerExcel(file).subscribe({
                next: (dados) => {
                    const atendimentos = this.parseAtendimentos(dados);
                    const atuais = this.atendimentosSubject.value;
                    this.atendimentosSubject.next([...atuais, ...atendimentos]);
                    observer.next(atendimentos);
                    observer.complete();
                },
                error: (err) => observer.error(err)
            });
        });
    }

    importarAvaliacao(file: File): Observable<Avaliacao[]> {
        return new Observable(observer => {
            this.arquivoService.lerExcel(file).subscribe({
                next: (dados) => {
                    const avaliacoes = this.parseAvaliacoes(dados);
                    const atuais = this.avaliacoesSubject.value;
                    this.avaliacoesSubject.next([...atuais, ...avaliacoes]);
                    observer.next(avaliacoes);
                    observer.complete();
                },
                error: (err) => observer.error(err)
            });
        });
    }

    // ─── PARSING ──────────────────────────────────────────────────

    private parseAtendimentos(dados: any[]): Atendimento[] {
        // Implementar parsing do Excel
        return dados.map(row => ({
            protocolo: row['Protocolo'] || '',
            nome: row['Nome'] || '',
            departamento: row['Departamento'] || '',
            atendente: row['Atendente'] || '',
            dataCriacao: new Date(row['Data_Criacao']),
            dataFinalizacao: row['Data_Finalizacao'] ? new Date(row['Data_Finalizacao']) : undefined,
            status: row['Status'] || 'aberto',
            tipo: row['Tipo'] || 'humano'
        }));
    }

    private parseAvaliacoes(dados: any[]): Avaliacao[] {
        return dados.map(row => ({
            id: row['Id'] || 0,
            atendimentoId: row['AtendimentoId'] || 0,
            nota: parseFloat(row['Nota']) || 0,
            departamento: row['Departamento'] || '',
            data: new Date(row['Data']),
            comentario: row['Comentario']
        }));
    }

    // ─── FILTROS ──────────────────────────────────────────────────

    aplicarFiltros(atendimentos: Atendimento[], filtros: FilterValues): Atendimento[] {
        return atendimentos.filter(a => {
            if (filtros.departamento && a.departamento !== filtros.departamento) return false;
            if (filtros.atendente && a.atendente !== filtros.atendente) return false;
            if (filtros.status) {
                if (filtros.status === 'finalizado' && a.status !== 'finalizado') return false;
                if (filtros.status === 'aberto' && a.status !== 'aberto') return false;
                if (filtros.status === 'humano' && a.tipo !== 'humano') return false;
                if (filtros.status === 'robo' && a.tipo !== 'robo') return false;
            }
            if (filtros.dataIni) {
                const data = new Date(a.dataCriacao);
                const ini = new Date(filtros.dataIni);
                ini.setHours(0, 0, 0, 0);
                if (data < ini) return false;
            }
            if (filtros.dataFim) {
                const data = new Date(a.dataCriacao);
                const fim = new Date(filtros.dataFim);
                fim.setHours(23, 59, 59, 999);
                if (data > fim) return false;
            }
            if (filtros.search) {
                const search = filtros.search.toLowerCase();
                return a.nome.toLowerCase().includes(search) ||
                    a.protocolo.toLowerCase().includes(search) ||
                    (a.telefone && a.telefone.includes(search));
            }
            return true;
        });
    }

    atualizarFiltros(filtros: FilterValues): void {
        this.filtrosSubject.next({ ...this.filtrosSubject.value, ...filtros });
    }

    limparFiltros(): void {
        this.filtrosSubject.next({});
    }

    // ─── ESTATÍSTICAS ─────────────────────────────────────────────

    calcularStats(atendimentos: Atendimento[]): AtendimentoStats {
        const total = atendimentos.length;
        const humanos = atendimentos.filter(a => a.tipo === 'humano' && a.status === 'finalizado');
        const robos = atendimentos.filter(a => a.tipo === 'robo' && a.status === 'finalizado');
        const emAberto = atendimentos.filter(a => a.status === 'aberto');

        const tempos = humanos
            .filter(a => a.dataCriacao && a.dataFinalizacao)
            .map(a => {
                const criacao = new Date(a.dataCriacao);
                const finalizacao = new Date(a.dataFinalizacao!);
                return (finalizacao.getTime() - criacao.getTime()) / 60000;
            });

        const tma = tempos.length > 0
            ? tempos.reduce((a, b) => a + b, 0) / tempos.length
            : 0;

        const esperas = atendimentos
            .filter(a => a.status === 'aberto' || a.tipo === 'robo')
            .map(a => {
                const criacao = new Date(a.dataCriacao);
                const agora = new Date();
                return (agora.getTime() - criacao.getTime()) / 60000;
            });

        const tme = esperas.length > 0
            ? esperas.reduce((a, b) => a + b, 0) / esperas.length
            : 0;

        return { total, humanos: humanos.length, robos: robos.length, emAberto: emAberto.length, tma, tme };
    }
}