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
 * Nível de acesso do usuário no sistema (ex: ADMIN, GESTOR, OPERADOR).
 * Separado em tabela própria para permitir evolução de permissões sem
 * alterar a estrutura de Usuario.
 */
@Entity
@Table(name = "niveis_usuario")
public class NivelUsuario extends PanacheEntity {

    @Column(nullable = false, unique = true, length = 50)
    public String nome;
}
