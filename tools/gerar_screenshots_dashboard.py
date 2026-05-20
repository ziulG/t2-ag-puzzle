"""Captura screenshots do dashboard Streamlit usando Playwright headless.

Pré-requisito: o dashboard precisa estar rodando em http://localhost:8501.
Uso:
    1. Em outro terminal: python main.py dashboard
    2. Aqui: python tools/gerar_screenshots_dashboard.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "screenshots"
OUT.mkdir(exist_ok=True, parents=True)

URL = "http://localhost:8501"

SECOES = [
    ("1. Visão Geral", "dashboard_01_visao_geral.png"),
    ("2. Convergência", "dashboard_02_convergencia.png"),
    ("3. Comparação de Configurações", "dashboard_03_comparacao.png"),
    ("4. Heatmap de Parâmetros", "dashboard_04_heatmap.png"),
    ("5. Análise por Caso", "dashboard_05_por_caso.png"),
    ("6. Inspeção Individual", "dashboard_06_inspecao.png"),
]


def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1600, "height": 900})
        try:
            page.goto(URL, wait_until="networkidle", timeout=60_000)
        except Exception as exc:
            print(f"Não consegui acessar {URL}: {exc}", file=sys.stderr)
            print("Suba o dashboard antes: `python main.py dashboard` em outro terminal.")
            browser.close()
            return 1

        # Streamlit precisa de tempo extra para renderizar gráficos matplotlib
        page.wait_for_timeout(4000)

        # Screenshot full-page para visão geral
        full_path = OUT / "dashboard_full.png"
        page.screenshot(path=str(full_path), full_page=True)
        print(f"✓ {full_path.relative_to(ROOT)}")

        for titulo, nome in SECOES:
            try:
                el = page.locator(f"text={titulo}").first
                # Scroll explícito para o topo do viewport (scrollIntoView padrão do navegador)
                el.evaluate(
                    "el => el.scrollIntoView({block: 'start', behavior: 'instant'})"
                )
                # Espera re-render / animação
                page.wait_for_timeout(1200)
                target = OUT / nome
                page.screenshot(path=str(target), full_page=False)
                print(f"✓ {target.relative_to(ROOT)}")
            except Exception as exc:
                print(f"⚠ Falha em '{titulo}': {exc}", file=sys.stderr)

        browser.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
