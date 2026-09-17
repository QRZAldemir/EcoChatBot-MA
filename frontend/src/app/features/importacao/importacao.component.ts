// src/app/features/importacao/importacao.component.ts

export class ImportacaoComponent {
  
  // ... outros códigos do componente ...

  /**
   * Processa uma imagem extraindo o texto via OCR (Tesseract.js)
   * O 'import' dinâmico garante que a biblioteca pesada só seja 
   * baixada pelo navegador quando o usuário realmente clicar no botão.
   */
  async processarOCR(arquivo: File): Promise<string> {
    try {
      // 1. Carrega a biblioteca dinamicamente (Lazy Loading)
      const { createWorker } = await import('tesseract.js');
      
      // 2. Inicia o worker em Português ('por')
      const worker = await createWorker('por');
      
      // 3. Reconhece o texto na imagem
      const { data: { text } } = await worker.recognize(arquivo);
      
      // 4. Encerra o worker para liberar a memória do navegador
      await worker.terminate();
      
      return text; // Retorna o texto extraído
      
    } catch (error) {
      console.error('Falha no processo de OCR:', error);
      throw new Error('Não foi possível processar a imagem. Tente uma imagem mais nítida.');
    }
  }
}