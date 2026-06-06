package br.ma.ecochatbot.dto;

import java.util.List;

public record MensagemMenuDTO(
    List<MensagemConteudoDTO> mensagens,
    String telefone,
    String lid,
    Long cliente_id,
    String conexao,
    String nome,
    String menu_id
) {}
