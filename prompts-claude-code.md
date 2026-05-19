# Prompts para Claude Code — Projeto 8-Puzzle AG

> Cada prompt assume `roadmap-8puzzle-ag.md` no contexto. Cole um de cada vez, aprove a Phase 0, depois libera a execução.

---

## Prompt 1 — Fundação (Puzzle + Testes)

```
@roadmap-8puzzle-ag.md

Vamos começar a Fase 1 do projeto (Fundação — Domínio do Puzzle).

ANTES DE QUALQUER CÓDIGO, faça uma Phase 0:
1. Releia a Fase 0 e Fase 1 do roadmap
2. Liste exatamente quais arquivos vai criar e qual o conteúdo conceitual de cada um
3. Aponte qualquer dúvida ou decisão de design que queira confirmar comigo antes de codar
4. Não escreva código ainda — só análise

Após eu aprovar a Phase 0, implemente:

**Estrutura do projeto:**
- Crie a estrutura de pastas conforme a Fase 0 do roadmap (puzzle/, ga/, experiment/, viz/, tests/)
- requirements.txt mínimo (só o necessário pra fase 1: pytest)
- README.md básico com instruções de setup
- .gitignore Python

**Implementação completa do módulo puzzle/:**
- estado.py: representação como tuple, constantes (GOAL, etc)
- movimentos.py: Enum Direcao, validação, aplicação
- heuristicas.py: distancia_manhattan, distancia_hamming, eh_soluvel
- goal.py: eh_objetivo

**Testes em tests/test_puzzle.py:**
- Pelo menos os testes listados na Fase 6 do roadmap (seção "Puzzle (essencial)")
- Adicione mais casos de borda que julgar relevantes
- Inclua docstrings explicando o que cada teste valida

**Restrições:**
- Python 3.11+
- Zero bibliotecas externas além de pytest
- Type hints em tudo
- Sem código comentado/dead code

**Critério de aceite:**
- `pytest tests/test_puzzle.py -v` retorna 100% verde
- Cobertura conceitual de todas as funções listadas no roadmap
- Estrutura de pastas conforme roadmap

Após implementar, rode os testes e me mostre o output.
```

---

## Prompt 2 — Motor do AG (Fitness Simples)

```
@roadmap-8puzzle-ag.md

Vamos pra Fase 2 do projeto (Motor do AG).

A Fase 1 (puzzle) já está implementada e testada. Vamos construir o motor do AG por cima.

ANTES DE QUALQUER CÓDIGO, faça uma Phase 0:
1. Releia a Fase 2 e Fase 3 do roadmap
2. Confirme a estrutura dos arquivos do módulo ga/ que vai criar
3. Aponte como cada operador (seleção, crossover, mutação) vai ser chamado pelo engine
4. Confirme a assinatura da função de fitness (vai receber config? vai retornar quais dados?)
5. Não escreva código ainda — só análise

Após eu aprovar a Phase 0, implemente:

**config.py:**
- Dataclass GAConfig completa conforme Fase 3 do roadmap
- Enums TipoSelecao e TipoCrossover
- Valores default exatamente como no roadmap

**Módulo ga/ completo:**
- cromossomo.py: encode/decode bits ↔ direções, geração aleatória
- populacao.py: inicialização, avaliação em lote
- selecao.py: torneio E roleta (ambos implementados)
- crossover.py: um-ponto E uniforme (ambos implementados)
- mutacao.py: bit flip por probabilidade
- elitismo.py: extração dos top N
- engine.py: loop principal, retorna histórico completo

**IMPORTANTE — Fitness nessa fase:**
- Implementar versão SIMPLES: apenas (max_score - manhattan_no_melhor_estado)
- NÃO adicionar penalidades de inválidos ou comprimento ainda
- NÃO adicionar bônus de resolveu ainda
- O fitness composto entra no Prompt 3 — aqui é só validar que o motor funciona

**Engine — requisitos do retorno:**
- Histórico por geração: melhor fitness, fitness médio, diversidade (desvio padrão), melhor cromossomo
- Indicação de parada (qual critério disparou)
- Melhor cromossomo final + estado alcançado + sequência de movimentos decodificada

**Testes em tests/test_ga.py:**
- Conforme Fase 6 do roadmap (seção "GA (importante)")
- Teste estatístico do torneio (1000 amostragens)
- Teste de que crossover preserva comprimento
- Teste de elitismo

**Teste de integração em tests/test_integration.py:**
- Roda AG num puzzle de ~5 movimentos do goal
- Com seed fixa, deve resolver dentro de 200 gerações
- Marque como teste lento (pytest mark slow)

**Restrições:**
- Zero bibliotecas de AG (DEAP, PyGAD, etc) — implementação manual
- Pode usar random/math da stdlib
- Type hints em tudo
- ga/ NÃO importa nada de puzzle/ diretamente — recebe fitness como callable injetado

**Critério de aceite:**
- `pytest -v` todo verde
- Rodar AG manualmente num puzzle fácil resolve consistentemente
- Histórico do engine tem todas as métricas necessárias pra próxima fase

Após implementar, rode os testes e mostre o output. Depois rode um AG num puzzle de exemplo e mostre a curva de convergência em texto (gráfico fica pra Fase 4).
```

---

## Prompt 3 — Fitness Composto + Experimentação

```
@roadmap-8puzzle-ag.md

Vamos pra Fase 3 do projeto (Fitness composto + Experimentação).

As Fases 1 e 2 já estão implementadas. O AG já resolve puzzles fáceis com fitness simples. Agora refinamos o fitness e construímos a camada de experimentação.

ANTES DE QUALQUER CÓDIGO, faça uma Phase 0:
1. Releia a Fase 2 (seção Fitness) e Fase 4 do roadmap
2. Explique como o fitness composto vai mudar e por quê
3. Liste a estrutura dos arquivos de experiment/ que vai criar
4. Defina o schema do CSV/JSON de saída (quais colunas exatamente)
5. Confirme como o batch runner vai gerenciar múltiplas execuções (paralelo via multiprocessing? sequencial?)
6. Não escreva código ainda — só análise

Após eu aprovar a Phase 0, implemente:

**Refinar fitness em ga/ (modificar função de fitness ou engine):**
- Fitness composto conforme Fase 2 do roadmap:
  - MAX_SCORE - manhattan_melhor_estado - α × movimentos_invalidos - β × passos_ate_melhor + BONUS_RESOLVEU
- Pegar α, β, MAX_SCORE, BONUS_RESOLVEU do GAConfig
- Decodificação do cromossomo deve guardar o MELHOR estado intermediário (menor Manhattan), não só o final
- Contar movimentos inválidos durante a simulação

**Módulo experiment/ completo:**
- runner.py: classe Runner que executa UMA configuração com UMA seed e retorna RunResult
- batch.py: classe BatchRunner que executa várias configs × várias seeds × vários puzzles
- metricas.py: agregação estatística (média, desvio, taxa de sucesso por config)

**RunResult deve conter:**
- Config usada (serializada)
- Estado inicial do puzzle
- Resolveu sim/não
- Gerações executadas
- Tempo total
- Histórico geração-a-geração
- Melhor cromossomo + sequência de movimentos decodificada (só os válidos)
- Manhattan final

**Persistência:**
- Resultados salvos em CSV (uma linha por execução) E JSON (detalhes completos)
- Pasta de saída: results/<timestamp>/
- Histórico por geração em arquivo separado pra não inchar o CSV principal

**Casos de teste pré-definidos:**
- Crie casos_teste.py com pelo menos 3 puzzles:
  - Fácil: ~5 movimentos do goal
  - Médio: ~15 movimentos
  - Difícil: ~25 movimentos
- Todos devem passar pela verificação de solvabilidade
- Hardcode eles (não gera aleatório aqui)

**Testes:**
- Atualize test_ga.py se a interface do fitness mudou
- Adicione test_experiment.py: Runner executa sem erro, gera RunResult válido, CSV é gerado e lido corretamente

**Script principal:**
- experiment/run_all.py: roda o batch completo conforme a Fase 4 do roadmap (Torneio vs Roleta × 3 taxas de mutação × 3 casos × 10 seeds)
- Mostra progress bar no terminal (tqdm permitido — é UX, não AG)

**Restrições:**
- tqdm permitido pra progress bar
- Sem libs de AG
- Tempo de execução total do batch: aceitável até ~30min, otimize se passar muito disso

**Critério de aceite:**
- Phase 0 aprovada antes de codar
- Testes todos verdes
- `python -m experiment.run_all` gera CSVs e JSONs em results/<timestamp>/
- Pelo menos o caso fácil tem taxa de sucesso > 80%
- O CSV abre limpo no pandas e tem todas as colunas combinadas na Phase 0

Após implementar, rode o batch e mostre um sample do CSV gerado + estatísticas básicas (taxa de sucesso por config).
```

---

## Prompt 4 — Visualizações (Pygame + Dashboard)

```
@roadmap-8puzzle-ag.md

Vamos pra Fase 5 do projeto (Visualizações). Última fase de código.

As Fases 1, 2 e 3 estão implementadas. Já temos CSVs com resultados de experimentos em results/<timestamp>/. Agora vamos visualizar tudo.

ANTES DE QUALQUER CÓDIGO, faça uma Phase 0:
1. Releia a Fase 5 do roadmap
2. Explique como o Pygame vai consumir um RunResult (vai ler do JSON? receber direto?)
3. Liste exatamente quais telas/gráficos o dashboard Streamlit vai ter
4. Confirme se o dashboard lê dos CSVs/JSONs salvos ou se também pode rodar AG ao vivo
5. Aponte qualquer ajuste necessário no formato dos arquivos salvos na Fase 3
6. Não escreva código ainda — só análise

Após eu aprovar a Phase 0, implemente:

**viz/pygame_anim.py:**
- Renderiza tabuleiro 3x3 estilizado
- Recebe path de um JSON de RunResult ou um RunResult em memória
- Anima a sequência de movimentos do melhor cromossomo
- Delay configurável entre movimentos (~300ms default)
- Painel lateral com:
  - Estado inicial
  - Estado objetivo
  - Contador de movimentos atual / total
  - Fitness do cromossomo
  - Indicação de "resolveu" no final
- Controles: SPACE pausa/continua, R reinicia, ESC sai
- Tabuleiro com cores: peças coloridas, vazio destacado

**viz/dashboard.py (Streamlit):**
- Sidebar:
  - Seletor de pasta de results/ (lista as execuções disponíveis)
  - Filtros: caso (fácil/médio/difícil), tipo seleção, taxa mutação
- Página principal com seções:
  1. Visão Geral: tabela resumo, taxa de sucesso global, tempo médio
  2. Convergência: gráfico de melhor fitness × geração (média ± desvio sobre execuções), uma linha por config selecionada
  3. Comparação de Configurações: barras de taxa de sucesso, boxplot de gerações até resolver
  4. Heatmap de Parâmetros: taxa de mutação × tipo de crossover → taxa de sucesso
  5. Análise por Caso: mesmas métricas separadas por dificuldade do puzzle
  6. Inspeção Individual: seletor de execução específica, mostra a curva de convergência daquela run e link pra rodar no Pygame

**main.py:**
- CLI com subcomandos:
  - `python main.py run` — roda o batch completo
  - `python main.py animate <path-to-json>` — abre Pygame com aquela run
  - `python main.py dashboard` — sobe o Streamlit
  - `python main.py test` — roda pytest

**Atualizar requirements.txt:**
- Adicionar: pygame, streamlit, matplotlib, pandas
- Travar versões

**Atualizar README.md:**
- Como instalar (pip install -r requirements.txt)
- Como rodar cada parte (run, animate, dashboard, test)
- Estrutura do projeto
- Print de cada tela do dashboard
- Screenshot do Pygame

**Restrições:**
- Pygame e Streamlit liberados (visualização, não AG)
- Matplotlib OK dentro do Streamlit
- Pandas OK pra manipular os CSVs no dashboard
- Sem libs de AG

**Critério de aceite:**
- Phase 0 aprovada antes de codar
- `python main.py animate <json>` mostra o puzzle se resolvendo visualmente
- `python main.py dashboard` sobe uma página web funcional com todas as seções
- README.md atualizado com screenshots
- Tudo roda fim-a-fim sem erro

Após implementar, gere screenshots do Pygame em ação e de cada seção do dashboard. Esses prints vão direto pro relatório.
```

---

## Dicas de Uso

**Padrão de cada prompt:**
1. Cola o prompt no Claude Code
2. Espera a Phase 0 (sem código)
3. Revisa, aponta ajustes ou aprova
4. Libera a implementação ("aprovado, pode codar")
5. Roda os critérios de aceite
6. Só passa pro próximo quando os testes da fase atual estão verdes

**Entre prompts:** dá um `/clear` no Claude Code se o contexto começar a pesar. O `.md` do roadmap continua sendo a fonte da verdade.

**Se algo der errado:** pede pra ele voltar à Phase 0 daquele prompt, releia o roadmap, e replaneje. Não tenta consertar com patches sucessivos — refaz a análise.
