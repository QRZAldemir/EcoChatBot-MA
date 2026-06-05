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
 * Canal de atendimento do EcoChatBot (ex: Ambulatório, Exames, Ouvidoria, Portaria).
 * Cada canal possui um menu de opções configurável (arquivo JSON) e pertence
 * a um Departamento responsável.
 *
 * Os canais definem QUAL fluxo conversacional o paciente percorre no WhatsApp.
 */
@Entity
@Table(name = "canais")
public class Canal extends PanacheEntity {

    @Column(nullable = false, length = 100)
    public String nome;

    public String descricao;

    // Arquivo JSON com as opções do menu deste canal (ex: menu_ambulatorio.json)
    @Column(name = "arquivo_menu")
    public String arquivoMenu;

    // Canal pertence a um departamento — LAZY para não carregar desnecessariamente
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "departamento_id")
    public Departamento departamento;

    @Column(nullable = false)
    public boolean ativo = true;
}
