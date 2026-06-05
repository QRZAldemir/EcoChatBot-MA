/*
 * EcoChatBot MA — Testes de Unidade | TDD com JUnit 5 + Mockito
 * Autor  : Aldemir Queiroz
 * Início : 29/09/2025
 * Stack  : Java 17 + Quarkus 3.9 · JUnit 5 · Mockito
 *
 * O que é testado aqui: DepartamentoService — regras de negócio isoladas do banco.
 * O repositório é SUBSTITUÍDO por um Mock (objeto falso controlado pelo teste),
 * permitindo testar o serviço sem banco de dados real.
 */
package br.ma.ecochatbot.service;

import br.ma.ecochatbot.dto.DepartamentoDTO;
import br.ma.ecochatbot.entity.Departamento;
import br.ma.ecochatbot.repository.DepartamentoRepository;
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
import static org.mockito.Mockito.*;

/*
 * @ExtendWith(MockitoExtension.class) — ativa o Mockito para esta classe de teste.
 * Sem isso, os @Mock e @InjectMocks abaixo não funcionariam.
 */
@ExtendWith(MockitoExtension.class)
@DisplayName("DepartamentoService — testes de unidade")
class DepartamentoServiceTest {

    /*
     * @Mock — cria um "dublê" do repositório. Não acessa banco real.
     * Controlamos exatamente o que ele retorna em cada teste.
     */
    @Mock
    private DepartamentoRepository repository;

    /*
     * @InjectMocks — cria uma instância real do Service e injeta o @Mock acima.
     * Testamos o comportamento REAL do serviço, com dependências simuladas.
     */
    @InjectMocks
    private DepartamentoService service;

    // =========================================================================
    // listar()
    // =========================================================================

    @Test
    @DisplayName("listar() deve retornar todos os departamentos cadastrados")
    void listar_deveRetornarTodosOsDepartamentos() {
        // GIVEN: o repositório retornará esta lista quando listAll() for chamado
        List<Departamento> esperado = List.of(
            departamentoComId(1L, "Ambulatório"),
            departamentoComId(2L, "Exames")
        );
        when(repository.listAll()).thenReturn(esperado);

        // WHEN: chamamos o serviço
        List<Departamento> resultado = service.listar();

        // THEN: verificamos o resultado E que o repositório foi chamado corretamente
        assertThat(resultado).hasSize(2);
        assertThat(resultado.get(0).nome).isEqualTo("Ambulatório");
        verify(repository).listAll(); // garante que o serviço de fato consultou o repositório
    }

    @Test
    @DisplayName("listar() deve retornar lista vazia quando não há departamentos")
    void listar_deveRetornarListaVazia_quandoNaoHaDepartamentos() {
        when(repository.listAll()).thenReturn(List.of());

        assertThat(service.listar()).isEmpty();
    }

    // =========================================================================
    // buscarPorId()
    // =========================================================================

    @Test
    @DisplayName("buscarPorId() deve retornar o departamento quando ele existe")
    void buscarPorId_deveRetornarDepartamento_quandoExiste() {
        Departamento departamento = departamentoComId(1L, "Ouvidoria");
        when(repository.findByIdOptional(1L)).thenReturn(Optional.of(departamento));

        Optional<Departamento> resultado = service.buscarPorId(1L);

        assertThat(resultado).isPresent();
        assertThat(resultado.get().nome).isEqualTo("Ouvidoria");
    }

    @Test
    @DisplayName("buscarPorId() deve retornar Optional vazio quando não existe")
    void buscarPorId_deveRetornarVazio_quandoNaoExiste() {
        when(repository.findByIdOptional(99L)).thenReturn(Optional.empty());

        assertThat(service.buscarPorId(99L)).isEmpty();
    }

    // =========================================================================
    // criar()
    // =========================================================================

    @Test
    @DisplayName("criar() deve persistir departamento com todos os campos do DTO")
    void criar_devePersistirDepartamentoComDadosDoDTO() {
        DepartamentoDTO dto = new DepartamentoDTO("Portaria", "Controle de entrada", true);

        /*
         * ArgumentCaptor: captura o objeto real passado para o mock.
         * Permite verificar exatamente O QUE foi enviado ao repositório,
         * não apenas se o método foi chamado.
         */
        ArgumentCaptor<Departamento> captor = ArgumentCaptor.forClass(Departamento.class);

        service.criar(dto);

        verify(repository).persist(captor.capture());
        Departamento salvo = captor.getValue();
        assertThat(salvo.nome).isEqualTo("Portaria");
        assertThat(salvo.descricao).isEqualTo("Controle de entrada");
        assertThat(salvo.ativo).isTrue();
    }

    @Test
    @DisplayName("criar() deve criar departamento inativo quando ativo=false no DTO")
    void criar_deveCriarDepartamentoInativo_quandoAtivoFalse() {
        DepartamentoDTO dto = new DepartamentoDTO("Arquivo", "Departamento desativado", false);
        ArgumentCaptor<Departamento> captor = ArgumentCaptor.forClass(Departamento.class);

        service.criar(dto);

        verify(repository).persist(captor.capture());
        assertThat(captor.getValue().ativo).isFalse();
    }

    // =========================================================================
    // atualizar()
    // =========================================================================

    @Test
    @DisplayName("atualizar() deve atualizar os campos quando o departamento existe")
    void atualizar_deveAtualizarCampos_quandoDepartamentoExiste() {
        Departamento existente = departamentoComId(1L, "Nome Antigo");
        when(repository.findByIdOptional(1L)).thenReturn(Optional.of(existente));

        Optional<Departamento> resultado = service.atualizar(1L,
            new DepartamentoDTO("Nome Novo", "Descrição nova", true));

        assertThat(resultado).isPresent();
        assertThat(resultado.get().nome).isEqualTo("Nome Novo");
        assertThat(resultado.get().descricao).isEqualTo("Descrição nova");
    }

    @Test
    @DisplayName("atualizar() deve retornar Optional vazio quando departamento não existe")
    void atualizar_deveRetornarVazio_quandoDepartamentoNaoExiste() {
        when(repository.findByIdOptional(99L)).thenReturn(Optional.empty());

        assertThat(service.atualizar(99L, new DepartamentoDTO("X", "Y", true))).isEmpty();
    }

    // =========================================================================
    // deletar()
    // =========================================================================

    @Test
    @DisplayName("deletar() deve retornar true quando o departamento existe")
    void deletar_deveRetornarTrue_quandoDepartamentoExiste() {
        when(repository.deleteById(1L)).thenReturn(true);

        assertThat(service.deletar(1L)).isTrue();
        verify(repository).deleteById(1L);
    }

    @Test
    @DisplayName("deletar() deve retornar false quando o departamento não existe")
    void deletar_deveRetornarFalse_quandoDepartamentoNaoExiste() {
        when(repository.deleteById(99L)).thenReturn(false);

        assertThat(service.deletar(99L)).isFalse();
    }

    // =========================================================================
    // Helpers — evitam repetição de código nos testes
    // =========================================================================

    private Departamento departamentoComId(Long id, String nome) {
        Departamento d = new Departamento();
        d.id = id;
        d.nome = nome;
        d.ativo = true;
        return d;
    }
}
