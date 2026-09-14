// ============================================================================
// CONFIGURAÇÃO DE AMBIENTE
// ============================================================================

export const ambiente = {
  producao: false,
  // Em produção, esta URL será substituída (ex: via variáveis de build ou docker)
  apiUrl: 'http://localhost:9001/api',
  evolutionApiUrl: 'http://localhost:8080',
  timeout: 30000
};