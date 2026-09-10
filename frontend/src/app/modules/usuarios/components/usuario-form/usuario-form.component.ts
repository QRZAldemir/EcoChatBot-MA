import { Component, EventEmitter, Output, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { UsuarioService } from '../../../../core/services/usuario.service';
import { DepartamentoService } from '../../../../core/services/departamento.service';
import { CanalService } from '../../../../core/services/canal.service';
import { TurnoService } from '../../../../core/services/turno.service';
import { Departamento } from '../../../../core/models/departamento.model';
import { Canal } from '../../../../core/models/canal.model';
import { Turno } from '../../../../core/models/turno.model';

@Component({
  selector: 'app-usuario-form',
  templateUrl: './usuario-form.component.html',
  styleUrls: ['./usuario-form.component.scss']
})
export class UsuarioFormComponent implements OnInit {
  @Output() usuarioSalvo = new EventEmitter<void>();

  usuarioForm: FormGroup;
  departamentos: Departamento[] = [];
  canais: Canal[] = [];
  turnos: Turno[] = [];
  fotoPreview: string | null = null;
  fotoPlaceholder = true;

  conexoes = [
    { value: '67-3416-7800', label: '67 3416-7800 — Oficial' },
    { value: '67-3416-7801', label: '67 3416-7801 — Suporte' }
  ];

  constructor(
    private fb: FormBuilder,
    private usuarioService: UsuarioService,
    private deptoService: DepartamentoService,
    private canalService: CanalService,
    private turnoService: TurnoService
  ) {
    this.usuarioForm = this.criarForm();
  }

  ngOnInit(): void {
    this.carregarDados();
  }

  private criarForm(): FormGroup {
    return this.fb.group({
      nome: ['', Validators.required],
      usuario: ['', Validators.required],
      email: ['', [Validators.required, Validators.email]],
      senha: ['', [Validators.required, Validators.minLength(6)]],
      senhaConf: ['', Validators.required],
      depto: ['', Validators.required],
      canal: ['', Validators.required],
      tipo: ['atendente', Validators.required],
      status: ['ativo', Validators.required],
      conexao: ['', Validators.required],
      conexaoPadrao: [''],
      turno: ['']
    }, { validators: this.senhasCoincidem });
  }

  private senhasCoincidem(group: FormGroup): { [key: string]: boolean } | null {
    const senha = group.get('senha')?.value;
    const conf = group.get('senhaConf')?.value;
    return senha === conf ? null : { senhasNaoCoincidem: true };
  }

  private carregarDados(): void {
    this.deptoService.departamentos$.subscribe(deptos => {
      this.departamentos = deptos.filter(d => d.status === 'ativo');
    });

    this.canalService.canais$.subscribe(canais => {
      this.canais = canais.filter(c => c.status === 'ativo');
    });

    this.turnoService.turnos$.subscribe(turnos => {
      this.turnos = turnos.filter(t => t.status === 'ativo');
    });
  }

  onFotoSelecionada(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files[0]) {
      const reader = new FileReader();
      reader.onload = (e) => {
        this.fotoPreview = e.target?.result as string;
        this.fotoPlaceholder = false;
      };
      reader.readAsDataURL(input.files[0]);
    }
  }

  salvar(): void {
    if (this.usuarioForm.invalid) {
      Object.keys(this.usuarioForm.controls).forEach(key => {
        this.usuarioForm.get(key)?.markAsTouched();
      });
      return;
    }

    const formData = this.usuarioForm.value;
    const usuario = {
      nome: formData.nome,
      usuario: formData.usuario,
      email: formData.email,
      depto: formData.depto,
      canal: formData.canal,
      tipo: formData.tipo,
      status: formData.status,
      conexao: formData.conexao,
      turno: formData.turno,
      foto: this.fotoPreview || undefined
    };

    this.usuarioService.adicionarUsuario(usuario);
    this.usuarioSalvo.emit();
    this.limparForm();
  }

  limparForm(): void {
    this.usuarioForm.reset({
      tipo: 'atendente',
      status: 'ativo'
    });
    this.fotoPreview = null;
    this.fotoPlaceholder = true;
    // Reset do input file
    const fileInput = document.getElementById('inputFoto') as HTMLInputElement;
    if (fileInput) fileInput.value = '';
  }

  get nome() { return this.usuarioForm.get('nome'); }
  get usuario() { return this.usuarioForm.get('usuario'); }
  get email() { return this.usuarioForm.get('email'); }
  get senha() { return this.usuarioForm.get('senha'); }
  get senhaConf() { return this.usuarioForm.get('senhaConf'); }
  get depto() { return this.usuarioForm.get('depto'); }
  get canal() { return this.usuarioForm.get('canal'); }
  get conexao() { return this.usuarioForm.get('conexao'); }

  get conexaoSelecionada(): string {
    const val = this.usuarioForm.get('conexao')?.value;
    if (!val) return 'Nenhuma conexão selecionada.';
    const conn = this.conexoes.find(c => c.value === val);
    return conn ? `WhatsApp ${conn.label}` : 'Nenhuma conexão selecionada.';
  }

  get turnoSelecionado(): string {
    const val = this.usuarioForm.get('turno')?.value;
    if (!val) return 'Nenhum turno selecionado.';
    return `🕐 ${val}`;
  }
}