/*
 * EcoChatBot MA — Sistema de Atendimento Digital com IA
 * Autor  : Aldemir Queiroz
 * Início : 29/09/2025
 * Stack  : Java 17 + Quarkus 3.9 · Angular 17 (frontend: Diego Queiroz)
 *
 * Backend: DESENVOLVE APIs REST consumidas pelo frontend e por integrações
 * externas (WhatsApp Business / Evolution API · DeepSeek AI).
 */
package br.ma.ecochatbot.entity;

import io.quarkus.hibernate.orm.panache.PanacheEntity;
import jakarta.persistence.*;

/**
 * Operador ou gestor do EcoChatBot MA.
 * A senha NUNCA é armazenada em texto puro — apenas o hash BCrypt (senhaHash).
 * A autenticação compara a senha informada com o hash usando BcryptUtil.matches().
 *
 * Um usuário é vinculado a um Departamento e a um Canal para definir
 * quais atendimentos ele gerencia no dashboard.
 */
@Entity
@Table(name = "usuarios")
public class Usuario extends PanacheEntity {

    @Column(nullable = false, length = 150)
    public String nome;

    @Column(nullable = false, unique = true, length = 150)
    public String email;

    // Hash BCrypt — nunca texto puro. Ver UsuarioService.criar()
    @Column(name = "senha_hash", nullable = false)
    public String senhaHash;

    @Column(length = 20)
    public String telefone;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "nivel_id")
    public NivelUsuario nivel;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "departamento_id")
    public Departamento departamento;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "canal_id")
    public Canal canal;

    @Column(nullable = false)
    public boolean ativo = true;
}
