# Skill: playwright-rpa

## Objetivo

Orientar tarefas de automação de browser com Playwright no ConnectLang RPA Bot: escolha de
locators, mecanismos de espera, sessão persistente, captura de screenshots de falha e timeouts.
Esta skill é o ponto de entrada para qualquer task que interaja com o browser.

---

## Quando usar

- A task envolve navegação no ConnectLang (fluxo de matrícula, atualização de registros, relatórios).
- É necessário decidir qual locator usar para um elemento da página.
- A task exige configurar ou validar a sessão persistente do browser.
- É preciso implementar waits, timeouts ou captura de screenshot de falha.
- A task adiciona ou corrige lógica em `src/connectlang_rpa/services/` ou `locators/`.

---

## Entradas esperadas

- Descrição do fluxo ou step de automação a implementar.
- Nome do arquivo de locators ou service a criar/modificar.
- Contexto do elemento HTML alvo (texto visível, role, label, placeholder ou atributo estável).
- Comportamento esperado em caso de falha (retry, abort, log e continuar).

---

## Saída esperada

- Código Python com Playwright síncrono, sem `time.sleep()` como sincronização.
- Locators definidos em `src/connectlang_rpa/locators/<page>.py`.
- Lógica de fluxo em `src/connectlang_rpa/services/<flow>_service.py`.
- Screenshots nomeadas `{flow}_{step}_{timestamp}.png` salvas em `screenshots/`.
- Log estruturado com `structlog` para cada item: identificador, status, timestamp.

---

## Checklist

- [ ] Locator usa hierarquia correta: `get_by_role` → `get_by_label` → `get_by_placeholder` →
      `get_by_text` → CSS semântico (`data-testid`, `name`, `id`).
- [ ] Nenhum XPath absoluto (`/html/body/div[3]/...`).
- [ ] Nenhuma classe CSS de utilidade (`.mt-4`, `.flex`, `.text-gray-500`).
- [ ] Nenhum `time.sleep()` substituindo wait semântico do Playwright.
- [ ] Waits explícitos: `wait_for_selector`, `wait_for_load_state`, `expect(locator).to_be_visible()`.
- [ ] Timeout explícito nas ações críticas; exceção descritiva em caso de timeout.
- [ ] Screenshot capturada imediatamente antes de levantar exceção de serviço.
- [ ] Sessão criada com `launch_persistent_context()`; diretório de perfil não versionado.
- [ ] Falha de item isolada: não interrompe o batch; log de erro estruturado e continua.
- [ ] Retry com `tenacity`: `stop` (máximo de tentativas) e `wait` (backoff) definidos.

---

## Limitações

- Não automatizar login Google, OAuth, captcha ou qualquer mecanismo de autenticação externa.
- Não interagir com plataformas fora do ConnectLang.
- Não misturar API síncrona e assíncrona do Playwright sem decisão arquitetural documentada.
- Não commitar screenshots, perfil de browser ou logs reais.