export type StatusConexao = 'conectada' | 'desconectada' | 'aguardando';

export interface Conexao {
  id: number;
  nome: string;
  telefone?: string;
  tipo: string;                 // whatsapp
  conexao: string;              // waba | qrcode
  atendimento: string;          // automatico | manual
  status: StatusConexao;
  padrao: boolean;              // número administrativo principal da empresa
  ativo: boolean;
  criadoEm?: string;
  fila: number;
  recebimentoMin: number;
}

export interface ConexaoQRCode {
  conexao: Conexao;
  qrcodeBase64?: string;
  pairingCode?: string;
  simulado: boolean;
  mensagem?: string;
}
