/*
 * EcoChatBot MA — Sistema de Atendimento Digital com IA
 * Autor  : Aldemir Queiroz
 * Início : 29/09/2025
 * Stack  : Java 17 + Quarkus 3.9 · Angular 17 (frontend: Diego Queiroz)
 */
package br.ma.ecochatbot.repository;

import br.ma.ecochatbot.entity.Usuario;
import io.quarkus.hibernate.orm.panache.PanacheRepository;
import jakarta.enterprise.context.ApplicationScoped;

import java.util.List;
import java.util.Optional;

/**
 * Repositório de Usuario com consultas customizadas usando a sintaxe
 * do Panache (JPQL simplificado) — sem precisar escrever EntityManager manualmente.
 */
@ApplicationScoped
public class UsuarioRepository implements PanacheRepository<Usuario> {

    // Busca por email — usado na autenticação. Optional evita NullPointerException.
    public Optional<Usuario> findByEmail(String email) {
        return find("email", email).firstResultOptional();
    }

    // ILIKE = case-insensitive, equivalente ao ilike() do Python/SQLAlchemy
    public List<Usuario> findByNome(String nome) {
        return list("lower(nome) like lower(?1)", "%" + nome + "%");
    }

    public List<Usuario> findByDepartamento(Long departamentoId) {
        return list("departamento.id", departamentoId);
    }

    public List<Usuario> findByCanal(Long canalId) {
        return list("canal.id", canalId);
    }

    public List<Usuario> findAtivos() {
        return list("ativo", true);
    }
}
