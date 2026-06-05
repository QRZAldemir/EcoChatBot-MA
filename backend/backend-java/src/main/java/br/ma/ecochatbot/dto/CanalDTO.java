/*
 * EcoChatBot MA — Sistema de Atendimento Digital com IA
 * Autor  : Aldemir Queiroz
 * Início : 29/09/2025
 * Stack  : Java 17 + Quarkus 3.9 · Angular 17 (frontend: Diego Queiroz)
 */
package br.ma.ecochatbot.dto;

/**
 * DTO de Canal — carrega os dados vindos do frontend Angular via requisição REST.
 * O departamentoId é uma referência (FK) — o serviço busca a entidade antes de associar.
 */
public class CanalDTO {

    private String nome;
    private String descricao;
    private String arquivoMenu;
    private Long departamentoId;
    private boolean ativo = true;

    public CanalDTO() {}

    public CanalDTO(String nome, String descricao, String arquivoMenu, Long departamentoId, boolean ativo) {
        this.nome = nome;
        this.descricao = descricao;
        this.arquivoMenu = arquivoMenu;
        this.departamentoId = departamentoId;
        this.ativo = ativo;
    }

    public String getNome() { return nome; }
    public void setNome(String nome) { this.nome = nome; }

    public String getDescricao() { return descricao; }
    public void setDescricao(String descricao) { this.descricao = descricao; }

    public String getArquivoMenu() { return arquivoMenu; }
    public void setArquivoMenu(String arquivoMenu) { this.arquivoMenu = arquivoMenu; }

    public Long getDepartamentoId() { return departamentoId; }
    public void setDepartamentoId(Long departamentoId) { this.departamentoId = departamentoId; }

    public boolean isAtivo() { return ativo; }
    public void setAtivo(boolean ativo) { this.ativo = ativo; }
}
