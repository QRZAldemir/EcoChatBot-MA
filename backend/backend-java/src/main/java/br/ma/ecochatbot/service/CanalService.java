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

import br.ma.ecochatbot.dto.CanalDTO;
import br.ma.ecochatbot.entity.Canal;
import br.ma.ecochatbot.entity.Departamento;
import br.ma.ecochatbot.repository.CanalRepository;
import br.ma.ecochatbot.repository.DepartamentoRepository;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import jakarta.transaction.Transactional;
import jakarta.ws.rs.NotFoundException;

import java.util.List;
import java.util.Optional;

/**
 * Serviço de negócio para Canal de atendimento.
 *
 * Responsabilidade: validar regras de negócio antes de persistir.
 * Exemplo: ao criar/atualizar um canal com departamentoId, verifica se
 * o departamento existe — lança NotFoundException se não existir,
 * que o Quarkus converte automaticamente em HTTP 404.
 */
@ApplicationScoped
public class CanalService {

    @Inject
    CanalRepository canalRepository;

    @Inject
    DepartamentoRepository departamentoRepository;

    public List<Canal> listar() {
        return canalRepository.listAll();
    }

    public Optional<Canal> buscarPorId(Long id) {
        return canalRepository.findByIdOptional(id);
    }

    @Transactional
    public Canal criar(CanalDTO dto) {
        Canal canal = new Canal();
        canal.nome = dto.getNome();
        canal.descricao = dto.getDescricao();
        canal.arquivoMenu = dto.getArquivoMenu();
        canal.ativo = dto.isAtivo();

        if (dto.getDepartamentoId() != null) {
            // Valida existência do departamento antes de associar
            canal.departamento = buscarDepartamento(dto.getDepartamentoId());
        }

        canalRepository.persist(canal);
        return canal;
    }

    @Transactional
    public Optional<Canal> atualizar(Long id, CanalDTO dto) {
        return canalRepository.findByIdOptional(id).map(canal -> {
            canal.nome = dto.getNome();
            canal.descricao = dto.getDescricao();
            canal.arquivoMenu = dto.getArquivoMenu();
            canal.ativo = dto.isAtivo();

            if (dto.getDepartamentoId() != null) {
                canal.departamento = buscarDepartamento(dto.getDepartamentoId());
            }

            return canal;
        });
    }

    @Transactional
    public boolean deletar(Long id) {
        return canalRepository.deleteById(id);
    }

    // Extrai a busca do departamento para evitar duplicação entre criar() e atualizar()
    private Departamento buscarDepartamento(Long id) {
        return departamentoRepository.findByIdOptional(id)
            .orElseThrow(() -> new NotFoundException("Departamento não encontrado: " + id));
    }
}
