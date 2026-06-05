/*
 * EcoChatBot MA — Testes de Unidade | TDD com JUnit 5 + Mockito
 * Autor  : Aldemir Queiroz
 * Início : 29/09/2025
 * Stack  : Java 17 + Quarkus 3.9 · JUnit 5 · Mockito
 *
 * O que é testado aqui: UsuarioService — com foco especial nas regras de segurança:
 * hash de senha (BCrypt), autenticação, bloqueio de usuário inativo.
 *
 * Estes testes demonstram práticas de TDD aplicadas a um sistema real de saúde,
 * onde a segurança das credenciais dos operadores é crítica.
 */
package br.ma.ecochatbot.service;

import br.ma.ecochatbot.dto.UsuarioDTO;
import br.ma.ecochatbot.entity.Departamento;
import br.ma.ecochatbot.entity.Usuario;
import br.ma.ecochatbot.repository.CanalRepository;
import br.ma.ecochatbot.repository.DepartamentoRepository;
import br.ma.ecochatbot.repository.UsuarioRepository;
import io.quarkus.elytron.security.common.BcryptUtil;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.List;
import java.util.Map;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
@DisplayName("UsuarioService — testes de unidade")
class UsuarioServiceTest {

    @Mock
    private UsuarioRepository usuarioRepository;

    @Mock
    private DepartamentoRepository departamentoRepository;

    @Mock
    private CanalRepository canalRepository;

    @InjectMocks
    private UsuarioService service;

    // =========================================================================
    // criar() — segurança de senha
    // =========================================================================

    @Test
    @DisplayName("criar() deve salvar senha como hash BCrypt — nunca em texto puro")
    void criar_deveSalvarSenhaComotHashBcrypt() {
        UsuarioDTO dto = new UsuarioDTO();
        dto.setNome("Ana Lima");
        dto.setEmail("ana@hospital-ma.br");
        dto.setSenha("minhasenha123");

        /*
         * ArgumentCaptor captura o objeto Usuario que foi enviado ao repositório.
         * Isso permite verificar COMO o objeto foi construído — não apenas SE persist() foi chamado.
         * É a técnica correta para validar transformações internas (como o hash da senha).
         */
        ArgumentCaptor<Usuario> captor = ArgumentCaptor.forClass(Usuario.class);

        service.criar(dto);

        verify(usuarioRepository).persist(captor.capture());
        Usuario salvo = captor.getValue();

        // A senha jamais pode estar em texto puro no banco
        assertThat(salvo.senhaHash)
            .as("senha não pode ser armazenada em texto puro")
            .isNotEqualTo("minhasenha123");

        // O hash deve validar a senha original (BCrypt é um hash de mão única verificável)
        assertThat(BcryptUtil.matches("minhasenha123", salvo.senhaHash))
            .as("BcryptUtil.matches() deve confirmar a senha original")
            .isTrue();
    }

    @Test
    @DisplayName("criar() deve associar departamento quando departamentoId é informado")
    void criar_deveAssociarDepartamento_quandoDepartamentoIdInformado() {
        Departamento depto = departamentoComId(3L, "Enfermagem");
        when(departamentoRepository.findByIdOptional(3L)).thenReturn(Optional.of(depto));

        UsuarioDTO dto = new UsuarioDTO();
        dto.setNome("Carlos");
        dto.setEmail("carlos@hospital-ma.br");
        dto.setSenha("senha456");
        dto.setDepartamentoId(3L);

        ArgumentCaptor<Usuario> captor = ArgumentCaptor.forClass(Usuario.class);
        service.criar(dto);

        verify(usuarioRepository).persist(captor.capture());
        assertThat(captor.getValue().departamento.nome).isEqualTo("Enfermagem");
    }

    // =========================================================================
    // autenticar() — regras de segurança de acesso
    // =========================================================================

    @Test
    @DisplayName("autenticar() deve retornar true com email e senha corretos")
    void autenticar_deveRetornarTrue_comCredenciaisCorretas() {
        String senhaOriginal = "senha_segura_99";
        Usuario usuario = usuarioAtivo(1L, "joao@hospital-ma.br", senhaOriginal);
        when(usuarioRepository.findByEmail("joao@hospital-ma.br")).thenReturn(Optional.of(usuario));

        assertThat(service.autenticar("joao@hospital-ma.br", senhaOriginal)).isTrue();
    }

    @Test
    @DisplayName("autenticar() deve retornar false com senha incorreta")
    void autenticar_deveRetornarFalse_comSenhaErrada() {
        Usuario usuario = usuarioAtivo(1L, "joao@hospital-ma.br", "senha_correta");
        when(usuarioRepository.findByEmail("joao@hospital-ma.br")).thenReturn(Optional.of(usuario));

        assertThat(service.autenticar("joao@hospital-ma.br", "senha_errada")).isFalse();
    }

    @Test
    @DisplayName("autenticar() deve retornar false quando email não existe no sistema")
    void autenticar_deveRetornarFalse_quandoEmailNaoExiste() {
        when(usuarioRepository.findByEmail("inexistente@hospital-ma.br")).thenReturn(Optional.empty());

        assertThat(service.autenticar("inexistente@hospital-ma.br", "qualquersenha")).isFalse();
    }

    @Test
    @DisplayName("autenticar() deve bloquear usuário inativo mesmo com senha correta")
    void autenticar_deveRetornarFalse_quandoUsuarioInativo() {
        // Regra de negócio: operadores desligados não podem acessar o sistema
        String senha = "senha123";
        Usuario usuario = usuarioAtivo(1L, "inativo@hospital-ma.br", senha);
        usuario.ativo = false; // desativa após criar o hash
        when(usuarioRepository.findByEmail("inativo@hospital-ma.br")).thenReturn(Optional.of(usuario));

        assertThat(service.autenticar("inativo@hospital-ma.br", senha)).isFalse();
    }

    // =========================================================================
    // atualizar() — senha não deve ser sobrescrita quando não informada
    // =========================================================================

    @Test
    @DisplayName("atualizar() não deve alterar senhaHash quando nova senha não é informada")
    void atualizar_naoDeveAlterarSenhaHash_quandoSenhaNaoInformada() {
        String hashOriginal = BcryptUtil.bcryptHash("senha_original");
        Usuario existente = new Usuario();
        existente.id = 1L;
        existente.nome = "Pedro";
        existente.email = "pedro@hospital-ma.br";
        existente.senhaHash = hashOriginal;
        existente.ativo = true;

        when(usuarioRepository.findByIdOptional(1L)).thenReturn(Optional.of(existente));

        UsuarioDTO dto = new UsuarioDTO();
        dto.setNome("Pedro Atualizado");
        dto.setEmail("pedro@hospital-ma.br");
        dto.setSenha(null); // senha não informada = não alterar

        service.atualizar(1L, dto);

        // O hash não deve ter sido alterado
        assertThat(existente.senhaHash).isEqualTo(hashOriginal);
        assertThat(existente.nome).isEqualTo("Pedro Atualizado");
    }

    // =========================================================================
    // agruparPorDepartamento() — base dos relatórios do dashboard
    // =========================================================================

    @Test
    @DisplayName("agruparPorDepartamento() deve agrupar corretamente por nome do departamento")
    void agruparPorDepartamento_deveAgruparCorretamente() {
        Departamento uti = departamentoComId(1L, "UTI");
        Departamento farmacia = departamentoComId(2L, "Farmácia");

        // Monta cenário: 2 na UTI, 1 na Farmácia, 1 sem departamento
        Usuario u1 = new Usuario(); u1.nome = "Ana";   u1.departamento = uti;
        Usuario u2 = new Usuario(); u2.nome = "Bruno"; u2.departamento = uti;
        Usuario u3 = new Usuario(); u3.nome = "Carla"; u3.departamento = farmacia;
        Usuario u4 = new Usuario(); u4.nome = "Diego"; u4.departamento = null;

        when(usuarioRepository.listAll()).thenReturn(List.of(u1, u2, u3, u4));

        Map<String, List<Usuario>> resultado = service.agruparPorDepartamento();

        assertThat(resultado).containsKeys("UTI", "Farmácia", "Sem Departamento");
        assertThat(resultado.get("UTI")).hasSize(2);
        assertThat(resultado.get("Farmácia")).hasSize(1);
        assertThat(resultado.get("Sem Departamento")).hasSize(1);
    }

    // =========================================================================
    // buscarPorId() / deletar()
    // =========================================================================

    @Test
    @DisplayName("buscarPorId() deve retornar Optional vazio quando usuário não existe")
    void buscarPorId_deveRetornarVazio_quandoUsuarioNaoExiste() {
        when(usuarioRepository.findByIdOptional(99L)).thenReturn(Optional.empty());

        assertThat(service.buscarPorId(99L)).isEmpty();
    }

    @Test
    @DisplayName("deletar() deve retornar true quando usuário existe")
    void deletar_deveRetornarTrue_quandoUsuarioExiste() {
        when(usuarioRepository.deleteById(1L)).thenReturn(true);

        assertThat(service.deletar(1L)).isTrue();
    }

    // =========================================================================
    // Helpers
    // =========================================================================

    private Usuario usuarioAtivo(Long id, String email, String senhaPlana) {
        Usuario u = new Usuario();
        u.id = id;
        u.nome = "Usuário Teste";
        u.email = email;
        u.senhaHash = BcryptUtil.bcryptHash(senhaPlana); // hash gerado aqui para o teste
        u.ativo = true;
        return u;
    }

    private Departamento departamentoComId(Long id, String nome) {
        Departamento d = new Departamento();
        d.id = id;
        d.nome = nome;
        d.ativo = true;
        return d;
    }
}
