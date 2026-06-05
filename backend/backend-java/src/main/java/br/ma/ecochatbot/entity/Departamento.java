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
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Table;

/**
 * Entidade que representa um departamento do hospital (ex: Ambulatório, Exames, Ouvidoria).
 * Estende PanacheEntity — o Quarkus injeta automaticamente o campo "id" (Long) e
 * os métodos de persistência herdados do padrão Active Record do Panache.
 *
 * Relacionamento: um Departamento pode ter vários Canais e vários Usuários.
 */
@Entity
@Table(name = "departamentos")
public class Departamento extends PanacheEntity {

    @Column(nullable = false, length = 100)
    public String nome;

    public String descricao;

    // Permite desativar sem excluir — padrão comum em sistemas hospitalares
    @Column(nullable = false)
    public boolean ativo = true;
}
