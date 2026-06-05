/*
 * EcoChatBot MA — Sistema de Atendimento Digital com IA
 * Autor  : Aldemir Queiroz
 * Início : 29/09/2025
 * Stack  : Java 17 + Quarkus 3.9 · Angular 17 (frontend: Diego Queiroz)
 */
package br.ma.ecochatbot.repository;

import br.ma.ecochatbot.entity.Canal;
import io.quarkus.hibernate.orm.panache.PanacheRepository;
import jakarta.enterprise.context.ApplicationScoped;

/**
 * Repositório de Canal — herda operações CRUD do Panache.
 * Consultas customizadas podem ser adicionadas aqui conforme necessidade.
 */
@ApplicationScoped
public class CanalRepository implements PanacheRepository<Canal> {
}
