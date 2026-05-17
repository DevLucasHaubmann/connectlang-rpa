# Skill: portfolio-docs

## Objetivo

Orientar a criação e atualização de documentação de portfólio do ConnectLang RPA Bot:
README principal, arquitetura, guia de uso e explicação de decisões técnicas. Linguagem
profissional, objetiva e adequada para apresentação a recrutadores ou avaliadores técnicos.

---

## Quando usar

- A task envolve criação ou atualização de `README.md`.
- A task envolve `docs/architecture.md` (decisões de arquitetura, stack, estrutura de pastas).
- A task envolve `docs/usage.md` (como configurar, executar e operar o bot).
- É necessário explicar uma decisão técnica do projeto de forma clara e justificada.
- A task marca a conclusão de um sprint ou milestone e exige atualização de documentação.

## Quando não usar

- A task envolve código Python ou automação de browser (delegar aos agentes especializados).
- A task é configuração interna de Claude Code (`.claude/`, hooks, settings).
- A task gera documentação de teste — usar `tests/manual/<flow>.md` diretamente.

---

## Entradas esperadas

- Contexto da funcionalidade ou decisão a documentar.
- Arquivo alvo: `README.md`, `docs/architecture.md` ou `docs/usage.md`.
- Nível de detalhe: visão geral (README) ou aprofundado (architecture, usage).
- Público-alvo: recrutador técnico, desenvolvedor ou operador do bot.

---

## Saída esperada

- Markdown estruturado com cabeçalhos, listas e blocos de código onde aplicável.
- Linguagem em inglês (padrão do projeto) ou português conforme convenção estabelecida.
- Explicações técnicas sem jargão desnecessário; decisões com justificativa explícita.
- Sem referências a plataformas, projetos ou empresas fora do escopo do ConnectLang RPA Bot.

---

## Checklist

- [ ] `README.md` cobre: propósito, stack, estrutura de pastas, pré-requisitos, como executar.
- [ ] `docs/architecture.md` cobre: decisões de design, camadas, fluxo de dados, regras de segurança.
- [ ] `docs/usage.md` cobre: configuração de variáveis de ambiente, execução, interpretação de logs,
      o que fazer em caso de falha.
- [ ] Decisões técnicas têm justificativa: por que Playwright síncrono, por que `src` layout,
      por que sessão persistente em vez de login automatizado.
- [ ] Nenhuma credencial, caminho real ou dado sensível na documentação.
- [ ] Linguagem direta, sem filler: afirmar o que o projeto faz e por quê.
- [ ] Exemplos de comando são funcionais e testáveis.

---

## Limitações

- Não gerar documentação de código (docstrings, comentários inline) — responsabilidade do código.
- Não criar documentação de testes manuais — usar `tests/manual/<flow>.md`.
- Não incluir referências a sistemas, plataformas ou projetos fora do escopo deste bot.
- Não usar linguagem promocional ou vaga ("poderoso", "robusto", "moderno") sem substância técnica.