# Rule: Playwright

## Session

- Use `launch_persistent_context()` for all browser sessions that require a logged-in state.
- Do not automate Google login, OAuth flows, captcha, or any authentication bypass.
- The persistent profile directory must never be version-controlled.

## API Style

- Use the synchronous Playwright API consistently throughout the project.
- Do not mix sync and async Playwright calls in the same codebase without an explicit architectural reason.

## Selectors — Preferred (in order)

1. `get_by_role()` with accessible name
2. `get_by_label()`
3. `get_by_placeholder()`
4. `get_by_text()` (for visible text only)
5. `locator("css=...")` with stable, semantic CSS attributes (e.g., `data-testid`, `name`, `id`)

## Selectors — Prohibited

- Absolute XPath (`/html/body/div[3]/...`).
- CSS class selectors tied to layout or utility styles (e.g., `.mt-4`, `.text-gray-500`, `.flex`).
- Index-based selectors (e.g., `nth-child(3)`) without a stable anchor.

## Waits and Synchronization

- Use Playwright's built-in waits: `wait_for_selector`, `wait_for_load_state`, `expect(locator).to_be_visible()`.
- Do not use `time.sleep()` as a substitute for semantic waits.
- Small `slow_mo` or operational delays between actions are acceptable when documented.

## Timeouts

- Set explicit timeouts for critical actions rather than relying on Playwright's global default.
- When a timeout fires, raise a descriptive exception — do not silently continue.

## Locators

- Locator definitions live in `locators/` — never inline selectors inside service or utility code.
- One locator file per page or feature area.

## Screenshots and Traces

- Capture a screenshot immediately before raising an exception in a service action.
- Name screenshots with context: `{flow}_{step}_{timestamp}.png`.
- Do not commit screenshots to version control.