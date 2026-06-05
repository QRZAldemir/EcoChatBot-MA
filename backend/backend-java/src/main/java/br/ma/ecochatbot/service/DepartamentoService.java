/*
 * EcoChatBot MA — Sistema de Atendimento Digital com IA
 * Autor  : Aldemir Queiroz
 * Início : 29/09/2025
 * Stack  : Java 17 + Quarkus 3.9 · Angular 17 (frontend: Diego Queiroz)
 *
 * Backend: DESENVOLVE APIs REST consumidas pelo frontend e por integrações
 * externas (WhatsApp Business / Evolution API · DeepSeek AI).
 */
package br.ma.ecochatbot.service;

import br.ma.ecochatbot.dto.DepartamentoDTO;
import br.ma.ecochatbot.entity.Departamento;
import br.ma.ecochatbot.repository.DepartamentoRepository;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import jakarta.transaction.Transactional;

import java.util.List;
import java.util.Optional;

/**
 * Serviço de negócio para Departamento.
 *
 * Padrão de arquitetura: Resource → Service → Repository → Banco.
 * O Resource (REST) chama o Service, que chama o Repository.
 * Isso permite testar o Service isoladamente (TDD com Mockito),
 * sem subir o banco de dados.
 *
 * @Transactional garante que operações de escrita sejam atômicas:
 * se qualquer linha falhar, tudo é revertido (rollback automático).
 */
@ApplicationScoped
public class DepartamentoService {

    @Inject
    DepartamentoRepository repository;

    public List<Departamento> listar() {
        return repository.listAll();
    }

    public Optional<Departamento> buscarPorId(Long id) {
        // Optional.empty() quando não existe — evita retornar null
        return repository.findByIdOptional(id);
    }

    @Transactional
    public Departamento criar(DepartamentoDTO dto) {
        Departamento departamento = new Departamento();
        departamento.nome = dto.getNome();
        departamento.descricao = dto.getDescricao();
        departamento.ativo = dto.isAtivo();
        repository.persist(departamento);
        return departamento;
    }

    @Transactional
    public Optional<Departamento> atualizar(Long id, DepartamentoDTO dto) {
        // map() só executa se o Optional tiver valor — elegante e seguro
        return repository.findByIdOptional(id).map(departamento -> {
            departamento.nome = dto.getNome();
            departamento.descricao = dto.getDescricao();
            departamento.ativo = dto.isAtivo();
            return departamento;
        });
    }

    @Transactional
    public boolean deletar(Long id) {
        return repository.deleteById(id);
    }
}
