/*
 * EcoChatBot MA — Sistema de Atendimento Digital com IA
 * Autor  : Aldemir Queiroz
 * Início : 29/09/2025
 * Stack  : Java 17 + Quarkus 3.9 · Angular 17 (frontend: Diego Queiroz)
 */
package br.ma.ecochatbot.repository;

import br.ma.ecochatbot.entity.Departamento;
import io.quarkus.hibernate.orm.panache.PanacheRepository;
import jakarta.enterprise.context.ApplicationScoped;

/**
 * Repositório de Departamento — padrão Repository do Quarkus Panache.
 * Herdando PanacheRepository<Departamento>, ganhamos os métodos CRUD prontos:
 * listAll(), findById(), persist(), deleteById(), etc.
 *
 * Separar o repositório do serviço é essencial para o TDD:
 * nos testes, o repositório é MOCKADO — o serviço é testado isoladamente,
 * sem precisar de banco de dados real.
 */
@ApplicationScoped
public class DepartamentoRepository implements PanacheRepository<Departamento> {
}
