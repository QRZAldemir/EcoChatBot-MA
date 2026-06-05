/*
 * EcoChatBot MA — Sistema de Atendimento Digital com IA
 * Autor  : Aldemir Queiroz
 * Início : 29/09/2025
 * Stack  : Java 17 + Quarkus 3.9 · Angular 17 (frontend: Diego Queiroz)
 */
package br.ma.ecochatbot.dto;

/**
 * DTO (Data Transfer Object) de Departamento.
 * Recebe os dados da requisição REST antes de persistir na entidade.
 * Separa o contrato da API do modelo de banco de dados.
 */
public class DepartamentoDTO {

    private String nome;
    private String descricao;
    private boolean ativo = true;

    public DepartamentoDTO() {}

    public DepartamentoDTO(String nome, String descricao, boolean ativo) {
        this.nome = nome;
        this.descricao = descricao;
        this.ativo = ativo;
    }

    public String getNome() { return nome; }
    public void setNome(String nome) { this.nome = nome; }

    public String getDescricao() { return descricao; }
    public void setDescricao(String descricao) { this.descricao = descricao; }

    public boolean isAtivo() { return ativo; }
    public void setAtivo(boolean ativo) { this.ativo = ativo; }
}
