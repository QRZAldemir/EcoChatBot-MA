/*
 * EcoChatBot MA — Testes de Unidade | TDD com JUnit 5 + Mockito
 * Autor  : Aldemir Queiroz
 * Início : 29/09/2025
 * Stack  : Java 17 + Quarkus 3.9 · JUnit 5 · Mockito
 *
 * O que é testado aqui: CanalService — incluindo validação de dependências
 * (departamento vinculado ao canal) e tratamento de erros via NotFoundException.
 */
package br.ma.ecochatbot.service;

import br.ma.ecochatbot.dto.CanalDTO;
import br.ma.ecochatbot.entity.Canal;
import br.ma.ecochatbot.entity.Departamento;
import br.ma.ecochatbot.repository.CanalRepository;
import br.ma.ecochatbot.repository.DepartamentoRepository;
import jakarta.ws.rs.NotFoundException;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.List;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
@DisplayName("CanalService — testes de unidade")
class CanalServiceTest {

    @Mock
    private CanalRepository canalRepository;

    // Dois mocks porque CanalService depende de dois repositórios
    @Mock
    private DepartamentoRepository departamentoRepository;

    @InjectMocks
    private CanalService service;

    // =========================================================================
    // listar()
    // =========================================================================

    @Test
    @DisplayName("listar() deve retornar todos os canais ativos e inativos")
    void listar_deveRetornarTodosOsCanais() {
        List<Canal> canais = List.of(
            canalComId(1L, "Ambulatório"),
            canalComId(2L, "Exames"),
            canalComId(3L, "Ouvidoria")
        );
        when(canalRepository.listAll()).thenReturn(canais);

        List<Canal> resultado = service.listar();

        assertThat(resultado).hasSize(3);
        verify(canalRepository).listAll();
    }

    // =========================================================================
    // buscarPorId()
    // =========================================================================

    @Test
    @DisplayName("buscarPorId() deve retornar o canal quando existe")
    void buscarPorId_deveRetornarCanal_quandoExiste() {
        Canal canal = canalComId(1L, "Ambulatório");
        when(canalRepository.findByIdOptional(1L)).thenReturn(Optional.of(canal));

        Optional<Canal> resultado = service.buscarPorId(1L);

        assertThat(resultado).isPresent();
        assertThat(resultado.get().nome).isEqualTo("Ambulatório");
    }

    @Test
    @DisplayName("buscarPorId() deve retornar Optional vazio quando canal não existe")
    void buscarPorId_deveRetornarVazio_quandoCanalNaoExiste() {
        when(canalRepository.findByIdOptional(99L)).thenReturn(Optional.empty());

        assertThat(service.buscarPorId(99L)).isEmpty();
    }

    // =========================================================================
    // criar()
    // =========================================================================

    @Test
    @DisplayName("criar() deve persistir canal sem departamento quando departamentoId é nulo")
    void criar_devePersistirCanal_semDepartamento() {
        CanalDTO dto = new CanalDTO("Portaria", "Canal da portaria", null, null, true);
        ArgumentCaptor<Canal> captor = ArgumentCaptor.forClass(Canal.class);

        service.criar(dto);

        verify(canalRepository).persist(captor.capture());
        Canal salvo = captor.getValue();
        assertThat(salvo.nome).isEqualTo("Portaria");
        assertThat(salvo.departamento).isNull();
        assertThat(salvo.ativo).isTrue();
    }

    @Test
    @DisplayName("criar() deve associar o departamento quando departamentoId é informado")
    void criar_deveAssociarDepartamento_quandoDepartamentoIdInformado() {
        Departamento depto = departamentoComId(5L, "Triagem");
        when(departamentoRepository.findByIdOptional(5L)).thenReturn(Optional.of(depto));

        CanalDTO dto = new CanalDTO("Triagem Rápida", "Canal de triagem", null, 5L, true);
        ArgumentCaptor<Canal> captor = ArgumentCaptor.forClass(Canal.class);

        service.criar(dto);

        verify(canalRepository).persist(captor.capture());
        assertThat(captor.getValue().departamento.nome).isEqualTo("Triagem");
    }

    @Test
    @DisplayName("criar() deve lançar NotFoundException quando departamento não existe")
    void criar_deveLancarNotFoundException_quandoDepartamentoNaoExiste() {
        /*
         * Teste de caminho de erro (sad path) — tão importante quanto o caminho feliz.
         * assertThatThrownBy verifica que a exceção correta é lançada.
         * A mensagem deve conter o ID para facilitar diagnóstico em produção.
         */
        when(departamentoRepository.findByIdOptional(99L)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> service.criar(new CanalDTO("X", "Y", null, 99L, true)))
            .isInstanceOf(NotFoundException.class)
            .hasMessageContaining("99");
    }

    // =========================================================================
    // atualizar()
    // =========================================================================

    @Test
    @DisplayName("atualizar() deve atualizar todos os campos quando canal existe")
    void atualizar_deveAtualizarDados_quandoCanalExiste() {
        Canal existente = canalComId(1L, "Nome Antigo");
        when(canalRepository.findByIdOptional(1L)).thenReturn(Optional.of(existente));

        Optional<Canal> resultado = service.atualizar(1L,
            new CanalDTO("Ambulatório Adulto", "Atualizado", "menu_v2.json", null, true));

        assertThat(resultado).isPresent();
        assertThat(resultado.get().nome).isEqualTo("Ambulatório Adulto");
        assertThat(resultado.get().arquivoMenu).isEqualTo("menu_v2.json");
    }

    @Test
    @DisplayName("atualizar() não deve chamar persist quando canal não existe")
    void atualizar_deveRetornarVazio_quandoCanalNaoExiste() {
        when(canalRepository.findByIdOptional(99L)).thenReturn(Optional.empty());

        Optional<Canal> resultado = service.atualizar(99L,
            new CanalDTO("X", "Y", null, null, true));

        assertThat(resultado).isEmpty();
        // never() — verifica que persist NUNCA foi chamado (o canal não existe)
        verify(canalRepository, never()).persist((Canal) any());
    }

    // =========================================================================
    // deletar()
    // =========================================================================

    @Test
    @DisplayName("deletar() deve retornar true quando canal existe")
    void deletar_deveRetornarTrue_quandoCanalExiste() {
        when(canalRepository.deleteById(1L)).thenReturn(true);

        assertThat(service.deletar(1L)).isTrue();
        verify(canalRepository).deleteById(1L);
    }

    @Test
    @DisplayName("deletar() deve retornar false quando canal não existe")
    void deletar_deveRetornarFalse_quandoCanalNaoExiste() {
        when(canalRepository.deleteById(99L)).thenReturn(false);

        assertThat(service.deletar(99L)).isFalse();
    }

    // =========================================================================
    // Helpers
    // =========================================================================

    private Canal canalComId(Long id, String nome) {
        Canal c = new Canal();
        c.id = id;
        c.nome = nome;
        c.ativo = true;
        return c;
    }

    private Departamento departamentoComId(Long id, String nome) {
        Departamento d = new Departamento();
        d.id = id;
        d.nome = nome;
        d.ativo = true;
        return d;
    }
}
