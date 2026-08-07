================================================================================
SKILL: TESTES UNITÁRIOS E ESTRUTURA AAA (METODOLOGIA DE QUALIDADE)
ARQUIVO: skill_testes_unitarios_aaa.txt
VERSÃO: 1.0.0
STACK: 
  BACKEND  : Python 3.12+ (pytest, pytest-mock, coverage, FastAPI TestClient)
  FRONTEND : Angular 17+ (Jest ou Karma/Jasmine)
OBSERVAÇÃO: O guia de referência original baseia-se em Java/Spring (JUnit, 
Mockito, H2). Esta skill traduz e adapta integralmente os conceitos, a pirâmide 
de testes e o padrão AAA para o ecossistema Python e Angular, respeitando a 
restrição de não utilização de Java estabelecida anteriormente.
================================================================================

--------------------------------------------------------------------------------
1. METADADOS E PRINCÍPIOS FUNDAMENTAIS
--------------------------------------------------------------------------------
name    : testes-unitarios-aaa
version : 1.0.0
triggers:
  - criar testes unitários
  - aplicar padrão AAA
  - configurar cobertura de código (coverage)
  - mockar dependências (repositórios, APIs externas)
  - estruturar pirâmide de testes

principios (Os 4 Pilares da Qualidade):
  1. Redução de bugs: Identificação de erros antes da implantação em produção.
  2. Confiabilidade: Aumento da confiança do usuário e da equipe técnica.
  3. Manutenção: Facilidade para modificar o código sem quebrar o existente.
  4. Segurança: Proteção contra efeitos colaterais em refatorações.

diretriz: "Fazer um código sem teste é como se você nem tivesse feito."

--------------------------------------------------------------------------------
2. A PIRÂMIDE DE TESTES
--------------------------------------------------------------------------------
A estratégia de testes é organizada por nível de complexidade, custo e velocidade.
No ecossistema Python/Angular, a pirâmide é implementada da seguinte forma:

CAMADA           | CUSTO/VEL. | O QUE VALIDA                 | FERRAMENTA
-----------------|------------|------------------------------|-------------------
Funcionais (E2E) | Alto/Lento | Cenários completos de negócio| Playwright/Cypress
Integração       | Médio      | API + Banco de Dados (Real)  | FastAPI TestClient
Unitários        | Baixo/Rápido| Menor unidade (funções/lógica)| pytest / Jest

Foco da Skill: A base da pirâmide (Testes Unitários). Devem representar a maior
parte da suíte por serem rápidos, baratos e totalmente isolados (sem latência de
rede ou dependência de bancos reais).

--------------------------------------------------------------------------------
3. O MÉTODO AAA (ARRANGE, ACT, ASSERT)
--------------------------------------------------------------------------------
Estrutura obrigatória de raciocínio lógico para cada caso de teste:

1. ARRANGE (Preparar):
   - O que fazer: Configurar o ambiente, instanciar objetos, preparar dados e
     simular dependências (Mocks).
   - No Python: Uso de `@pytest.fixture` para centralizar preparações (DRY) e
     `mocker` (pytest-mock) para isolar a unidade testada.

2. ACT (Agir):
   - O que fazer: Executar o método específico que está sendo testado sob as
     condições preparadas.
   - No Python: Chamada direta da função ou método da classe.

3. ASSERT (Validar):
   - O que fazer: Comparar o resultado obtido com o esperado e verificar se
     as dependências foram chamadas corretamente.
   - No Python: Uso da palavra-chave `assert` e métodos do Mock 
     (ex: `assert_called_once`).

--------------------------------------------------------------------------------
4. KIT DE FERRAMENTAS (ADAPTAÇÃO PYTHON/ANGULAR)
--------------------------------------------------------------------------------
Conceito do Guia (Java)  | Equivalente no Ecossistema Python/Angular
-------------------------|----------------------------------------------------
JUnit                    | pytest (Backend) / Jest ou Karma (Frontend)
Mockito (@Mock)          | pytest-mock (mocker) / unittest.mock (Backend)
@BeforeEach              | @pytest.fixture (Backend) / beforeEach (Frontend)
@Test                    | def test_nome_do_cenario(): (Backend) / it() (Front)
H2 (Banco em memória)    | SQLite em memória / TestContainers (Integração)
pom.xml                  | pyproject.toml / requirements-dev.txt (pip)

--------------------------------------------------------------------------------
5. APLICAÇÃO PRÁTICA: ANATOMIA DE UM TESTE (PYTHON)
--------------------------------------------------------------------------------
Exemplo adaptado do guia (ContaService), utilizando pytest e pytest-mock para
evitar chamadas reais ao banco de dados (Isolamento Total).

--- ARQUIVO: tests/services/test_conta_service.py ------------------------------
import pytest
from unittest.mock import MagicMock
from app.services.conta_service import ContaService
from app.models.conta import Conta

@pytest.fixture
def conta_exemplo():
    """ARRANGE: Preparação comum (DRY) via fixtures do pytest."""
    return Conta(titular="João", saldo=100.0)

@pytest.fixture
def mock_repo(mocker):
    """ARRANGE: Simulação do repositório (equivalente ao @Mock do Mockito)."""
    return mocker.MagicMock()

@pytest.fixture
def conta_service(mock_repo):
    """ARRANGE: Injeção de dependência (equivalente ao @InjectMocks)."""
    return ContaService(repository=mock_repo)

def test_deve_criar_uma_conta_com_sucesso(conta_service, mock_repo, conta_exemplo):
    # 1. ARRANGE (Configuração específica do Mock)
    mock_repo.save.return_value = conta_exemplo

    # 2. ACT (Ação)
    resultado = conta_service.criar_conta(conta_exemplo)

    # 3. ASSERT (Validação de estado e comportamento)
    assert resultado is not None
    assert resultado.titular == "João"
    assert resultado.saldo == 100.0
    
    # Verifica se o repositório foi chamado exatamente 1 vez com o objeto correto
    mock_repo.save.assert_called_once_with(conta_exemplo)

def test_deve_lancar_excecao_para_saldo_negativo(conta_service, mock_repo):
    # Testando o "caminho triste" (cenário de exceção)
    conta_invalida = Conta(titular="Maria", saldo=-50.0)
    
    with pytest.raises(ValueError, match="Saldo não pode ser negativo"):
        conta_service.criar_conta(conta_invalida)
        
    # Garante que o banco NUNCA foi chamado se a validação falhar
    mock_repo.save.assert_not_called()

--------------------------------------------------------------------------------
6. BENEFÍCIOS REAIS (SÍNTESE)
--------------------------------------------------------------------------------
[x] Identificação Rápida de Erros: O erro aparece durante o desenvolvimento,
    impedindo que chegue ao cliente.
[x] Feedback Rápido: O pytest executa milhares de testes unitários em 
    milissegundos, validando alterações instantaneamente.
[x] Melhoria do Design: Códigos difíceis de testar (alto acoplamento) forçam
    o engenheiro a reescrever a arquitetura para usar Injeção de Dependência.
[x] Documentação Viva: Os testes servem como exemplo prático e atualizado de
    como a regra de negócio deve se comportar.

--------------------------------------------------------------------------------
7. PRÓXIMOS PASSOS E ESTRATÉGIA DE COBERTURA
--------------------------------------------------------------------------------
1. Caminho Feliz vs. Caminho Triste: Não testar apenas o sucesso. É obrigatório
   testar todas as variações de `if/else`, tratamentos de exceção e validações
   de borda.
2. Testes de Integração: Após consolidar os unitários, validar a conversa real
   entre a API (FastAPI) e o Banco de Dados usando `TestClient` e bancos em
   memória (SQLite) ou TestContainers (PostgreSQL real em Docker).
3. CI/CD (Integração Contínua): Automatizar a execução do `pytest` e a geração
   de relatórios de cobertura (`coverage.py`) em pipelines (GitHub Actions,
   GitLab CI) para que cada commit seja validado.
4. Meta de Cobertura: Buscar 100% de cobertura de código nas camadas de 
   Serviço e Regras de Negócio.

--------------------------------------------------------------------------------
8. COMANDOS DE EXECUÇÃO (PYTHON)
--------------------------------------------------------------------------------
# Instalar ferramentas de teste
pip install pytest pytest-mock pytest-cov

# Executar todos os testes unitários com relatório de cobertura
pytest tests/ --cov=app --cov-report=term-missing

# Executar um teste específico
pytest tests/services/test_conta_service.py -v

================================================================================