import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, of } from 'rxjs';
import { Usuario } from '../models/usuario.model';

@Injectable({
  providedIn: 'root'
})
export class UsuarioService {
  private readonly STORAGE_KEY = 'ecochat_usuarios';
  private usuariosSubject = new BehaviorSubject<Usuario[]>([]);
  public usuarios$ = this.usuariosSubject.asObservable();

  constructor() {
    this.carregarUsuarios();
  }

  private carregarUsuarios(): void {
    const data = localStorage.getItem(this.STORAGE_KEY);
    const usuarios = data ? JSON.parse(data) : [];
    this.usuariosSubject.next(usuarios);
  }

  private salvarUsuarios(usuarios: Usuario[]): void {
    localStorage.setItem(this.STORAGE_KEY, JSON.stringify(usuarios));
    this.usuariosSubject.next(usuarios);
  }

  listar(filtros?: { nivel?: string; departamento?: string; departamentoId?: number; canalId?: number; status?: string; nome?: string }): Observable<Usuario[]> {
    const usuarios = this.filtrarUsuarios(filtros ?? {});
    return of(usuarios);
  }

  getUsuarios(): Usuario[] {
    return this.usuariosSubject.value;
  }

  getUsuarioById(id: number): Usuario | undefined {
    return this.usuariosSubject.value.find(u => u.id === id);
  }

  getUsuariosPorDepartamento(depto: string): Usuario[] {
    return this.usuariosSubject.value.filter(u => u.depto === depto);
  }

  getUsuariosPorCanal(canal: string): Usuario[] {
    return this.usuariosSubject.value.filter(u => u.canal === canal);
  }

  getUsuariosPorTurno(turno: string): Usuario[] {
    return this.usuariosSubject.value.filter(u => u.turno === turno);
  }

  getStats() {
    const usuarios = this.usuariosSubject.value;
    const deptos = new Set(usuarios.map(u => u.depto)).size;
    const canais = new Set(usuarios.map(u => u.canal)).size;
    return {
      total: usuarios.length,
      departamentos: deptos,
      canais: canais,
      conexoes: 1
    };
  }

  criar(usuario: Partial<Usuario>): Observable<Usuario> {
    const novoUsuario: Usuario = {
      ...usuario,
      id: Date.now(),
      nome: usuario.nome ?? 'Novo Usuário',
      usuario: usuario.usuario ?? 'novo.usuario',
      email: usuario.email ?? '',
      depto: usuario.depto ?? '',
      canal: usuario.canal ?? '',
      tipo: usuario.tipo ?? 'atendente',
      status: usuario.status ?? 'ativo',
      conexao: usuario.conexao ?? '',
      turno: usuario.turno ?? '',
      data: new Date().toLocaleDateString('pt-BR')
    } as Usuario;
    this.salvarUsuarios([...this.usuariosSubject.value, novoUsuario]);
    return of(novoUsuario);
  }

  atualizar(id: number, dados: Partial<Usuario>): Observable<Usuario | null> {
    const usuarios = this.usuariosSubject.value;
    const index = usuarios.findIndex(u => u.id === id);
    if (index === -1) return of(null);

    const atualizado = { ...usuarios[index], ...dados };
    usuarios[index] = atualizado;
    this.salvarUsuarios(usuarios);
    return of(atualizado);
  }

  deletar(id: number): Observable<boolean> {
    const usuarios = this.usuariosSubject.value.filter(u => u.id !== id);
    if (usuarios.length === this.usuariosSubject.value.length) return of(false);
    this.salvarUsuarios(usuarios);
    return of(true);
  }

  adicionarUsuario(usuario: Omit<Usuario, 'id'>): Usuario {
    const novoUsuario = {
      ...usuario,
      id: Date.now(),
      data: new Date().toLocaleDateString('pt-BR')
    } as Usuario;
    this.salvarUsuarios([...this.usuariosSubject.value, novoUsuario]);
    return novoUsuario;
  }

  atualizarUsuario(id: number, dados: Partial<Usuario>): Usuario | null {
    const usuarios = this.usuariosSubject.value;
    const index = usuarios.findIndex(u => u.id === id);
    if (index === -1) return null;

    const atualizado = { ...usuarios[index], ...dados };
    usuarios[index] = atualizado;
    this.salvarUsuarios(usuarios);
    return atualizado;
  }

  deletarUsuario(id: number): boolean {
    const usuarios = this.usuariosSubject.value.filter(u => u.id !== id);
    if (usuarios.length === this.usuariosSubject.value.length) return false;
    this.salvarUsuarios(usuarios);
    return true;
  }

  filtrarUsuarios(filtros: { nome?: string; depto?: string; departamentoId?: number; canalId?: number; status?: string; nivel?: string }): Usuario[] {
    let usuarios = this.usuariosSubject.value;

    if (filtros.nome) {
      const nome = filtros.nome.toLowerCase();
      usuarios = usuarios.filter(u =>
        (u.nome ?? '').toLowerCase().includes(nome) ||
        (u.usuario ?? '').toLowerCase().includes(nome)
      );
    }

    if (filtros.depto) {
      usuarios = usuarios.filter(u => (u.depto ?? '') === filtros.depto);
    }

    if (filtros.departamentoId != null) {
      usuarios = usuarios.filter(u => (u.departamentoId ?? 0) === filtros.departamentoId);
    }

    if (filtros.canalId != null) {
      usuarios = usuarios.filter(u => (u.canalId ?? 0) === filtros.canalId);
    }

    if (filtros.status) {
      usuarios = usuarios.filter(u => (u.status ?? 'ativo') === filtros.status);
    }

    if (filtros.nivel) {
      usuarios = usuarios.filter(u => (u.tipo ?? u.nivel ?? 'atendente') === filtros.nivel);
    }

    return usuarios;
  }

  agruparPorDepartamento(usuarios: Usuario[]): Map<string, Usuario[]> {
    const grupos = new Map<string, Usuario[]>();
    usuarios.forEach(usuario => {
      const nomeDepartamento = usuario.depto || usuario.departamentoId?.toString() || 'Sem departamento';
      const existentes = grupos.get(nomeDepartamento) ?? [];
      existentes.push(usuario);
      grupos.set(nomeDepartamento, existentes);
    });
    return grupos;
  }
}