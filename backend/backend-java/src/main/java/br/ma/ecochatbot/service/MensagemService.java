
      @Transactional
      public MensagemResponse enviarTemplate(MensagemTemplateDTO dto) {
          try {
              // Validar template ID
              if (dto.template_id() == null || dto.template_id().isEmpty()) {
                  return new MensagemResponse(
                      0,
                      "Template ID é obrigatório",
                      null
                  );
              }

              // Criar entidade de mensagem
              Mensagem mensagem = new Mensagem();
              mensagem.telefone = dto.contato_telefone();
              mensagem.lid = dto.template_id() + "-" + System.currentTimeMillis();
              mensagem.nome_cliente = dto.contato_nome();
              mensagem.conexao = dto.conexao_nome();
              mensagem.conteudo_texto = "Template: " + dto.template_id();
              mensagem.status = "PENDENTE";

              mensagemRepository.persist(mensagem);

              // Construir payload para Evolution API com template
              Map<String, Object> payload = Map.of(
                  "contato_nome", dto.contato_nome(),
                  "contato_telefone", dto.contato_telefone(),
                  "conexao_nome", dto.conexao_nome(),
                  "template_id", dto.template_id(),
                  "menu_id", dto.menu_id(),
                  "header_parameters", dto.header_parameters() != null ? dto.header_parameters() : List.of(),
                  "body_parameters", dto.body_parameters()
              );

              // Chamar Evolution API
              Map<String, Object> respostaEvolution = evolutionApiClient.enviarTemplate(payload);

              // Atualizar status
              mensagem.status = "ENVIADO";
              mensagem.id_evolution_api = (String) respostaEvolution.get("id");
              mensagem.atualizada_em = LocalDateTime.now();
              mensagemRepository.update(mensagem);

              return new MensagemResponse(
                  1,
                  null,
                  Map.of(
                      "mensagem_id", mensagem.id,
                      "status", "ENVIADO",
                      "template_id", dto.template_id(),
                      "evolution_id", respostaEvolution.get("id")
                  )
              );

          } catch (Exception e) {
              return new MensagemResponse(
                  0,
                  "Erro ao enviar template: " + e.getMessage(),
                  null
              );
          }
      }