/*
 * EcoChatBot MA — Sistema de Atendimento Digital com IA
 * Autor  : Aldemir Queiroz
 * Data   : 2026-06-06
 */
package br.ma.ecochatbot.dto;

import com.fasterxml.jackson.annotation.JsonInclude;

@JsonInclude(JsonInclude.Include.NON_NULL)
public record MensagemResponse(
    Integer codigo,
    String erro,
    Object dados
) {}
