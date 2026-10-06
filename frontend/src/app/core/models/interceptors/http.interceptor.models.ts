/**
 * EcoChatBot - Sistema de Atendimento
 * 
 * Arquivo: http.interceptor.models.ts
 * Descricao: Define o interceptor HTTP funcional para autenticacao e tratamento de erros.
 * Este arquivo contem a implementacao do HttpInterceptorFn (padrao Angular 17) para:
 * - Adicionar token JWT nas requisicoes (Authorization: Bearer)
 * - Tratar erros HTTP (401, 403, 404, 500, etc.) com mensagens amigaveis
 * - Redirecionar para /login em caso de sessao expirada (401)
 * - Log estruturado de erros para debug
 * 
 * Autor: Aldemir Querioz
 * Data: 2026-10-05
 * Versao: 2.0.0
 * 
 * NOTA TECNICA:
 * - Usa a forma FUNCIONAL (HttpInterceptorFn) - padrao Angular 17+
 * - Usa inject() para injecao de dependencias (Router)
 * - Usa RxJS para manipulacao de Observables (catchError, throwError)
 * - Compativel com backend FastAPI (trata error.error.detail)
 */

import {
  HttpInterceptorFn,
  HttpErrorResponse,
  HttpRequest,
  HttpHandlerFn,
} from '@angular/common/http';

import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';


/** Chave usada para ler/gravar o token no storage. Centralizada para evitar
 *  "números mágicos" — se um dia mudar para 'access_token', muda em 1 só lugar. */
const TOKEN_KEY = 'token';

/** Mapa de código HTTP → mensagem amigável em português.
 *  Usado como FALLBACK quando o backend não envia `detail`.
 *  Tipagem `Record<number, string>` garante chave numérica e valor string. */
const STATUS_MESSAGES: Record<number, string> = {
  0:   'Não foi possível conectar ao servidor. Verifique sua internet.', // erro de rede
  400: 'Requisição inválida.',
  401: 'Sessão expirada. Faça login novamente.',
  403: 'Você não tem permissão para realizar esta ação.',
  404: 'Recurso não encontrado.',
  500: 'Erro interno do servidor. Tente novamente mais tarde.',
  502: 'Servidor indisponível. Tente novamente mais tarde.',
  503: 'Serviço temporariamente indisponível.',
};

/**
 * Estende o HttpErrorResponse original (herda .status, .error, .message...)
 * e adiciona o campo `userMessage` com a mensagem amigável que o componente
 * deve exibir ao usuário final.
 *
 * Por que existe: substitui o `(error as any).userMessage` do código original.
 * Sem `any`, com tipagem forte. Quando o componente pegar o erro, ele SABE
 * que existe .userMessage — o TypeScript garante em tempo de compilação.
 */
export interface AppHttpError extends HttpErrorResponse {
  userMessage: string;
}

/**
 * Clona a requisição adicionando os headers apropriados:
 *   - Authorization: Bearer <token>  (se houver token)
 *   - Content-Type: application/json (APENAS quando o body NÃO é FormData)
 *
 * IMPORTANTE: requisições HTTP no Angular são IMUTÁVEIS. Você nunca modifica
 * diretamente — sempre clona via `req.clone()`.
 *
 * BUG CORRIGIDO: no código original, `Content-Type: application/json` era
 * forçado em TODA requisição, o que QUEBRAVA uploads de arquivo (FormData),
 * pois o browser precisa definir o Content-Type com o boundary correto.
 *
 * @param req   Requisição original
 * @param token Token JWT (ou null se não autenticado)
 * @returns     Nova requisição clonada com headers enriquecidos
 */
function enrichRequest(
  req: HttpRequest<unknown>,
  token: string | null,
): HttpRequest<unknown> {
  // Objeto temporário que vai acumular os headers a adicionar
  const headers: Record<string, string> = {};

  // Se tem token, adiciona o header de autorização
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  // Detecta se o body é FormData (upload de arquivo).
  // Se FOR FormData → NÃO define Content-Type (o browser define sozinho
  //                   com o boundary multipart correto).
  // Se NÃO for e ainda não tiver Content-Type → define como application/json.
  const isFormData = req.body instanceof FormData;
  if (!isFormData && !req.headers.has('Content-Type')) {
    headers['Content-Type'] = 'application/json';
  }

  // Clona a requisição original com os novos headers (imutabilidade)
  return req.clone({ setHeaders: headers });
}

/**
 * Resolve a mensagem amigável a ser exibida com base no status HTTP e no
 * corpo da resposta.
 *
 * ORDEM DE PRIORIDADE (a primeira que encontrar vence):
 *   1. `error.error.detail`  → padrão FastAPI (backend Python). Mais específico.
 *   2. `STATUS_MESSAGES[status]` → mensagem genérica do mapa.
 *   3. Fallback final → "Ocorreu um erro inesperado no servidor."
 *
 * @param error Erro HTTP recebido do backend
 * @returns     Mensagem em português pronta para exibir no toast
 */
function resolveUserMessage(error: HttpErrorResponse): string {
  // Tenta extrair o `detail` do corpo (padrão FastAPI).
  // O `?.` evita erro se error.error for null/undefined.
  const detail = (error.error as { detail?: string } | null)?.detail;
  if (detail) return detail;

  // Não achou detail → busca no mapa pelo status.
  // `??` retorna o fallback só se STATUS_MESSAGES[status] for null/undefined.
  return STATUS_MESSAGES[error.status] ?? 'Ocorreu um erro inesperado no servidor.';
}

/**
 * Trata sessão expirada (HTTP 401):
 *   1. Remove o token inválido do storage.
 *   2. Redireciona para /login.
 *
 * O `void` antes de router.navigate() indica intencionalmente que ignoramos
 * o retorno (uma Promise). Evita warning de lint "no-floating-promises".
 *
 * @param router Instância do Router (injetada no interceptor)
 */
function handleUnauthorized(router: Router): void {
  localStorage.removeItem(TOKEN_KEY);
  void router.navigate(['/login']);
}

/**
 * Interceptor HTTP funcional (padrão Angular 17).
 *
 * FLUXO DE EXECUÇÃO:
 *   Componente chama HTTP
 *          ↓
 *   [INTERCEPTOR] ← enriquece com token
 *          ↓
 *   Backend responde
 *          ↓
 *   [INTERCEPTOR] ← verifica se houve erro
 *          ↓
 *   Sucesso? → passa adiante (componente recebe resposta)
 *   Erro?    → 401? limpa sessão + redireciona
 *            → anexa userMessage amigável
 *            → repropaga ao componente
 *
 * @param req  A requisição HTTP que está passando
 * @param next O próximo handler da cadeia (quem realmente envia ao backend)
 * @returns    Observable da resposta HTTP
 */
export const httpInterceptor: HttpInterceptorFn = (
  req: HttpRequest<unknown>,
  next: HttpHandlerFn,
) => {
  // ---- ETAPA 1: Injeção de dependências (padrão Angular 17) ----
  const router = inject(Router);

  // ---- ETAPA 2: Lê o token atual do storage ----
  const token = localStorage.getItem(TOKEN_KEY);

  // ---- ETAPA 3: Clona a requisição com headers enriquecidos ----
  const enriched = enrichRequest(req, token);

  // ---- ETAPA 4: Envia a requisição adiante e escuta erros ----
  // `next(enriched)` → passa para o próximo handler (envia de fato).
  // `.pipe(catchError(...))` → intercepta QUALQUER erro que venha da resposta.
  return next(enriched).pipe(
    catchError((error: HttpErrorResponse) => {
      // ---- ETAPA 5: Log estruturado para debug ----
      // Formato: [HTTP 409] POST /api/instancias <mensagem>
      console.error(
        `[HTTP ${error.status}] ${req.method} ${req.url}`,
        error.message,
      );

      // ---- ETAPA 6: Tratamento específico de 401 ----
      // Sessão expirada → limpa token + redireciona para login
      if (error.status === 401) {
        handleUnauthorized(router);
      }

      // ---- ETAPA 7: Anexa mensagem amigável SEM destruir o erro ----
      // Faz cast seguro (não é `any`) para AppHttpError.
      // O erro original continua com .status, .error, .message etc.
      const enrichedError = error as AppHttpError;
      enrichedError.userMessage = resolveUserMessage(error);

      // ---- ETAPA 8: Repropaga o erro (agora enriquecido) ----
      // throwError usa arrow function (padrão RxJS 7+) para criar o Observable
      // de erro. Quem chamou (o componente) receberá este erro com .userMessage.
      return throwError(() => enrichedError);
    }),
  );
};