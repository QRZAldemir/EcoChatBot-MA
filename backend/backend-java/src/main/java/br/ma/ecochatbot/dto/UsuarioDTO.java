/*
 * EcoChatBot MA — Sistema de Atendimento Digital com IA
 * Autor  : Aldemir Queiroz
 * Início : 29/09/2025
 * Stack  : Java 17 + Quarkus 3.9 · Angular 17 (frontend: Diego Queiroz)
 */
package br.ma.ecochatbot.dto;

/**
 * DTO de Usuario. O campo "senha" recebe a senha em texto puro vinda do frontend.
 * O serviço converte para hash BCrypt ANTES de persistir — a entidade Usuario
 * nunca armazena senhaHash em texto puro.
 *
 * Em atualizações, senha=null significa "não alterar a senha atual".
 */
public class UsuarioDTO {

    private String nome;
    private String email;
    private String senha;
    private String telefone;
    private Long nivelId;
    private Long departamentoId;
    private Long canalId;
    private boolean ativo = true;

    public UsuarioDTO() {}

    public String getNome() { return nome; }
    public void setNome(String nome) { this.nome = nome; }

    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }

    public String getSenha() { return senha; }
    public void setSenha(String senha) { this.senha = senha; }

    public String getTelefone() { return telefone; }
    public void setTelefone(String telefone) { this.telefone = telefone; }

    public Long getNivelId() { return nivelId; }
    public void setNivelId(Long nivelId) { this.nivelId = nivelId; }

    public Long getDepartamentoId() { return departamentoId; }
    public void setDepartamentoId(Long departamentoId) { this.departamentoId = departamentoId; }

    public Long getCanalId() { return canalId; }
    public void setCanalId(Long canalId) { this.canalId = canalId; }

    public boolean isAtivo() { return ativo; }
    public void setAtivo(boolean ativo) { this.ativo = ativo; }
}
