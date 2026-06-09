#!/usr/bin/env bash
# Wrapper de execução do projeto 8-puzzle com AG.
# Cuida do venv automaticamente e expõe atalhos pros subcomandos do main.py.

set -euo pipefail

# Sempre roda a partir da raiz do projeto (onde o script está).
cd "$(dirname "$0")"

VENV_DIR=".venv"
PY_BIN="${VENV_DIR}/bin/python"
PIP_BIN="${VENV_DIR}/bin/pip"

cor() { printf "\033[1;36m%s\033[0m\n" "$1"; }
erro() { printf "\033[1;31m%s\033[0m\n" "$1" >&2; }

# ---- Setup do venv ----------------------------------------------------------
if [[ ! -d "${VENV_DIR}" ]]; then
  cor "→ Criando venv em ${VENV_DIR}..."
  python3 -m venv "${VENV_DIR}"
fi

# Marca de "deps já instaladas" — só reinstala se o requirements mudar.
HASH_ATUAL="$(shasum requirements.txt | awk '{print $1}')"
HASH_FILE="${VENV_DIR}/.req_hash"
if [[ ! -f "${HASH_FILE}" || "$(cat "${HASH_FILE}" 2>/dev/null)" != "${HASH_ATUAL}" ]]; then
  cor "→ Instalando dependências..."
  "${PIP_BIN}" install -q --upgrade pip
  "${PIP_BIN}" install -q -r requirements.txt
  echo "${HASH_ATUAL}" > "${HASH_FILE}"
fi

# ---- Despacho dos comandos --------------------------------------------------
COMANDO="${1:-help}"
shift || true

case "${COMANDO}" in
  run)
    cor "→ Rodando batch de experimentos..."
    # NOTA: chamamos o módulo direto pra evitar conflito de argparse
    # (main.py 'run' delega pra experiment.run_all, que reparseia sys.argv).
    "${PY_BIN}" -m experiment.run_all "$@"
    ;;

  animate|anim)
    cor "→ Animando a melhor execução (Pygame)..."
    "${PY_BIN}" main.py animate --latest "$@"
    ;;

  dashboard|dash)
    cor "→ Subindo dashboard Streamlit..."
    "${PY_BIN}" main.py dashboard "$@"
    ;;

  test|tests)
    cor "→ Rodando pytest..."
    "${PY_BIN}" main.py test "$@"
    ;;

  pdf|relatorio|report)
    cor "→ Gerando RELATORIO.pdf (pandoc + xelatex)..."
    bash scripts/gerar_pdf_relatorio.sh "$@"
    ;;

  all)
    cor "→ Pipeline completo: test → run → animate"
    "${PY_BIN}" main.py test
    "${PY_BIN}" -m experiment.run_all
    "${PY_BIN}" main.py animate --latest
    ;;

  help|-h|--help|"")
    cat <<EOF
Uso: ./run.sh <comando> [args...]

Comandos:
  run         Roda o batch completo de experimentos (resultados em results/)
  animate    Anima a melhor execução da pasta mais recente (Pygame)
  dashboard  Sobe o dashboard interativo Streamlit
  test       Roda a suíte de testes (pytest)
  pdf         Gera RELATORIO.pdf a partir do RELATORIO.md (pandoc + xelatex)
  all         Pipeline: testes → run → animate
  help       Mostra esta ajuda

Exemplos:
  ./run.sh run
  ./run.sh animate --delay 500
  ./run.sh pdf
  ./run.sh all
EOF
    ;;

  *)
    erro "Comando desconhecido: ${COMANDO}"
    erro "Use './run.sh help' pra ver os comandos disponíveis."
    exit 2
    ;;
esac
