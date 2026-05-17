from pathlib import Path
from playwright.sync_api import sync_playwright

profile_dir = Path("browser-profile")
profile_dir.mkdir(exist_ok=True)

with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        user_data_dir=str(profile_dir),
        headless=False,
    )
    page = context.new_page()
    page.goto("https://connectlang.com.br/aluno/vocabulario")
    input("Faça login manualmente, confirme que abriu o vocabulário e pressione Enter aqui...")
    context.close()
