-- Centraliza imagens que estão sozinhas em um parágrafo e limita a largura.
-- Usado com `--from=markdown-implicit_figures`: as imagens viram \includegraphics
-- simples (sem legenda automática), e as legendas em itálico já escritas logo
-- abaixo de cada imagem no RELATORIO.md fazem o papel de legenda.
function Para(el)
  if #el.content == 1 and el.content[1].t == "Image" then
    local img = el.content[1]
    if not img.attributes.width then
      img.attributes.width = "85%"
    end
    return {
      pandoc.RawBlock("latex", "\\begin{center}"),
      el,
      pandoc.RawBlock("latex", "\\end{center}"),
    }
  end
end
