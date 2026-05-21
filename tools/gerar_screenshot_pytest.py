"""Renderiza a saída de ``pytest -v`` como PNG estilo terminal.

Roda pytest no diretório do projeto, embute o stdout em um HTML com fundo
preto e fonte monoespaçada (contadores e PASSED em verde), e captura via
Playwright headless. Não introduz dependências novas — Playwright já é
usado por ``tools/gerar_screenshots_dashboard.py``.

Uso:
    python tools/gerar_screenshot_pytest.py
"""

from __future__ import annotations

import html as html_lib
import re
import subprocess
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "screenshots" / "pytest_verde.png"


def _rodar_pytest() -> str:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-v", "--color=no"],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
        check=False,
    )
    saida = proc.stdout
    if proc.stderr.strip():
        saida += "\n" + proc.stderr
    return saida


def _destacar(saida: str) -> str:
    seguro = html_lib.escape(saida)
    seguro = re.sub(r"\bPASSED\b", '<span class="ok">PASSED</span>', seguro)
    seguro = re.sub(r"(\d+ passed[^\n]*)", r'<span class="ok">\1</span>', seguro)
    seguro = re.sub(r"\bFAILED\b", '<span class="err">FAILED</span>', seguro)
    return seguro


HTML_TEMPLATE = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
body {{
    margin: 0;
    background: #0b0b0b;
    color: #e6e6e6;
    font-family: "SF Mono", "Menlo", "Consolas", monospace;
    font-size: 13px;
    line-height: 1.45;
    padding: 20px 28px;
}}
pre {{ margin: 0; white-space: pre-wrap; word-break: break-word; }}
.ok {{ color: #3dd66b; font-weight: 600; }}
.err {{ color: #ff5d5d; font-weight: 600; }}
</style></head>
<body><pre>{corpo}</pre></body></html>
"""


def main() -> int:
    bruto = _rodar_pytest()
    corpo = _destacar(bruto)
    html = HTML_TEMPLATE.format(corpo=corpo)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1200, "height": 800})
        page.set_content(html)
        page.wait_for_timeout(300)
        page.screenshot(path=str(OUT), full_page=True)
        browser.close()
    print(f"✓ {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
