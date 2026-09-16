// frontend/src/app/features/canais/canal-form.component.ts
import { FormBuilder, FormGroup, Validators } from '@angular/forms';

export class CanalFormComponent {
  canalForm: FormGroup;

  constructor(private fb: FormBuilder) {
    this.canalForm = this.fb.group({
      nome: ['', Validators.required],
      tipo: ['voip_telefonia', Validators.required],
      identificador: ['08001234567', Validators.required], // Número principal
      // O campo configuração recebe o objeto JSON estruturado
      configuracao: this.fb.group({
        pabx_type: ['asterisk_ari', Validators.required],
        api_base_url: ['http://192.168.1.10:8088/ari', Validators.required],
        api_user: ['eco_chatbot_user', Validators.required],
        api_secret: ['senha_segura_do_pabx', Validators.required],
        trunk_outbound: ['SIP/TroncoVivo', Validators.required],
        context_ura: ['eco_ura_entrada'],
        stt_provider: ['openai'],
        tts_provider: ['openai']
      })
    });
  }

  onSubmit() {
    if (this.canalForm.valid) {
      // O Angular envia isso como JSON no body da requisição POST /api/canais
      this.canalService.criarCanal(this.canalForm.value).subscribe(...);
    }
  }
}