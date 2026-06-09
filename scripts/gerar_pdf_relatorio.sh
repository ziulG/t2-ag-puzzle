 #!/usr/bin/env bash
# Gera RELATORIO.pdf a partir de RELATORIO.md usando pandoc + xelatex.
# Mantém o RELATORIO.md como fonte única: o pré-processamento é feito num
# arquivo temporário, sem tocar no original.

set -euo pipefail
cd "$(dirname "$0")/.."   # raiz do projeto

SRC="RELATORIO.md"
OUT="RELATORIO.pdf"
PANDOC_DIR="scripts/pandoc"

command -v pandoc   >/dev/null || { echo "ERRO: pandoc não encontrado." >&2; exit 1; }
command -v xelatex  >/dev/null || { echo "ERRO: xelatex não encontrado (instale o MacTeX/TeX Live)." >&2; exit 1; }
[[ -f "$SRC" ]] || { echo "ERRO: $SRC não encontrado." >&2; exit 1; }

TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT

# Pré-processa o markdown (sem tocar no original):
#  1. Remove o cabeçalho manual (título + bloco "## Sumário"), deixando o
#     conteúdo a partir de "## 1. Resumo". A capa vem do meta.yaml e o sumário
#     do --toc.
#  2. Escapa "A*" -> "A\*" FORA de blocos de código. Dentro de legendas em
#     itálico (*...*) o asterisco de "A*" colidiria com a ênfase do Markdown e
#     o "A-estrela" sumiria. Dentro de blocos ``` (ex.: a árvore de diretórios
#     com "A* baseline") nada é alterado.
awk '
  /^## 1\. Resumo/ { p = 1 }
  p {
    if ($0 ~ /^```/) { infence = !infence; print; next }
    if (!infence) { gsub(/A\*/, "A\\*") }
    print
  }
' "$SRC" > "$TMP"

# Capa derivada do cabeçalho do RELATORIO.md, para que o .md seja a ÚNICA fonte
# da verdade — editar título/autor/data no topo do .md atualiza a capa. Esses
# valores sobrescrevem os de meta.yaml (que ficam só como fallback). Usamos
# classe de caractere [*] em vez de \* para evitar avisos do awk.
TITULO=$(awk 'NR==1{sub(/^#[ \t]*/,"");print;exit}' "$SRC")
AUTOR=$(awk '/^[*][*]Autor:[*][*]/{sub(/^[*][*]Autor:[*][*][ \t]*/,"");print;exit}' "$SRC")
DATA=$(awk '/^[*][*]Data:[*][*]/{sub(/^[*][*]Data:[*][*][ \t]*/,"");print;exit}' "$SRC")
META_ARGS=()
if [[ -n "$TITULO" ]]; then META_ARGS+=(-M "title=$TITULO"); fi
if [[ -n "$AUTOR"  ]]; then META_ARGS+=(-M "author=$AUTOR"); fi
if [[ -n "$DATA"   ]]; then META_ARGS+=(-M "date=$DATA"); fi

echo "→ Compilando $OUT (pandoc + xelatex)..."
echo "  Capa (do cabeçalho do .md): título=\"$TITULO\" · autor=\"$AUTOR\" · data=\"$DATA\""
pandoc "$TMP" \
  --from=markdown-implicit_figures \
  --pdf-engine=xelatex \
  --toc --toc-depth=2 \
  --metadata-file="$PANDOC_DIR/meta.yaml" \
  ${META_ARGS[@]+"${META_ARGS[@]}"} \
  --include-in-header="$PANDOC_DIR/header.tex" \
  --lua-filter="$PANDOC_DIR/center-images.lua" \
  --resource-path=".:docs" \
  -o "$OUT"

echo "✓ Gerado: $OUT"
if command -v pdfinfo >/dev/null; then
  pdfinfo "$OUT" | awk '/^Pages:/ {print "  Páginas: " $2}'
fi
