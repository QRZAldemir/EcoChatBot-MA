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

import br.ma.ecochatbot.dto.UsuarioDTO;
import br.ma.ecochatbot.entity.Usuario;
import br.ma.ecochatbot.repository.CanalRepository;
import br.ma.ecochatbot.repository.DepartamentoRepository;
import br.ma.ecochatbot.repository.UsuarioRepository;
import io.quarkus.elytron.security.common.BcryptUtil;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import jakarta.transaction.Transactional;
import jakarta.ws.rs.NotFoundException;

import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.stream.Collectors;

/**
 * Serviço de Usuario — contém a regra de segurança mais crítica do sistema:
 * a proteção de senha via hash BCrypt.
 *
 * Segurança:
 *   - BcryptUtil.bcryptHash(senha) — transforma texto puro em hash irreversível
 *   - BcryptUtil.matches(senhaInformada, hashSalvo) — compara na autenticação
 *   - Usuários inativos não conseguem autenticar, mesmo com senha correta
 *
 * Agrupamento por departamento: usado nos relatórios do dashboard (SLA/TMA).
 */
@ApplicationScoped
public class UsuarioService {

    @Inject
    UsuarioRepository usuarioRepository;

    @Inject
    DepartamentoRepository departamentoRepository;

    @Inject
    CanalRepository canalRepository;

    public List<Usuario> listar() {
        return usuarioRepository.listAll();
    }

    public List<Usuario> listarAtivos() {
        return usuarioRepository.findAtivos();
    }

    public Optional<Usuario> buscarPorId(Long id) {
        return usuarioRepository.findByIdOptional(id);
    }

    public Optional<Usuario> buscarPorEmail(String email) {
        return usuarioRepository.findByEmail(email);
    }

    @Transactional
    public Usuario criar(UsuarioDTO dto) {
        Usuario usuario = new Usuario();
        usuario.nome = dto.getNome();
        usuario.email = dto.getEmail();
        // Converte para hash BCrypt — nunca armazena senha em texto puro
        usuario.senhaHash = BcryptUtil.bcryptHash(dto.getSenha());
        usuario.telefone = dto.getTelefone();
        usuario.ativo = dto.isAtivo();

        if (dto.getDepartamentoId() != null) {
            usuario.departamento = departamentoRepository.findByIdOptional(dto.getDepartamentoId())
                .orElseThrow(() -> new NotFoundException("Departamento não encontrado"));
        }

        if (dto.getCanalId() != null) {
            usuario.canal = canalRepository.findByIdOptional(dto.getCanalId())
                .orElseThrow(() -> new NotFoundException("Canal não encontrado"));
        }

        usuarioRepository.persist(usuario);
        return usuario;
    }

    @Transactional
    public Optional<Usuario> atualizar(Long id, UsuarioDTO dto) {
        return usuarioRepository.findByIdOptional(id).map(usuario -> {
            usuario.nome = dto.getNome();
            usuario.email = dto.getEmail();
            usuario.telefone = dto.getTelefone();
            usuario.ativo = dto.isAtivo();

            // Só atualiza a senha se uma nova foi informada — evita sobrescrever sem querer
            if (dto.getSenha() != null && !dto.getSenha().isBlank()) {
                usuario.senhaHash = BcryptUtil.bcryptHash(dto.getSenha());
            }

            if (dto.getDepartamentoId() != null) {
                usuario.departamento = departamentoRepository.findByIdOptional(dto.getDepartamentoId())
                    .orElseThrow(() -> new NotFoundException("Departamento não encontrado"));
            }

            if (dto.getCanalId() != null) {
                usuario.canal = canalRepository.findByIdOptional(dto.getCanalId())
                    .orElseThrow(() -> new NotFoundException("Canal não encontrado"));
            }

            return usuario;
        });
    }

    @Transactional
    public boolean deletar(Long id) {
        return usuarioRepository.deleteById(id);
    }

    /**
     * Autentica usuário por email e senha.
     * Retorna false se: email não existe, senha errada, ou usuário inativo.
     * A sequência usa Optional encadeado para evitar condicionais aninhados.
     */
    public boolean autenticar(String email, String senha) {
        return usuarioRepository.findByEmail(email)
            .filter(u -> u.ativo)                              // bloqueia usuário inativo
            .map(u -> BcryptUtil.matches(senha, u.senhaHash))  // compara com o hash
            .orElse(false);                                    // email não encontrado
    }

    /**
     * Agrupa usuários por nome do departamento — base dos relatórios do dashboard.
     * Usuários sem departamento vão para o grupo "Sem Departamento".
     */
    public Map<String, List<Usuario>> agruparPorDepartamento() {
        return usuarioRepository.listAll().stream()
            .collect(Collectors.groupingBy(u ->
                u.departamento != null ? u.departamento.nome : "Sem Departamento"
            ));
    }
}
