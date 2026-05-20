"""Animação Pygame do 8-Puzzle sendo resolvido pelo melhor cromossomo.

Lê um JSON de detalhe (results/<ts>/detalhes/<run_id>.json) e anima a sequência
de movimentos decodificados. Controles: SPACE pausa/continua, R reinicia, ESC sai.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pygame

from puzzle.goal import GOAL
from puzzle.movimentos import aplicar_movimento
from viz._io import (
    carregar_detalhe_json,
    mapear_direcoes,
    parse_estado_inicial,
)

# --- Paleta (monocromático sóbrio) ---
COR_FUNDO = (44, 62, 80)         # #2c3e50
COR_PECA = (52, 152, 219)        # #3498db
COR_VAZIO = (31, 45, 58)         # #1f2d3a
COR_BORDA = (52, 73, 94)         # #34495e
COR_TEXTO = (236, 240, 241)
COR_TEXTO_FRACO = (149, 165, 166)
COR_RESOLVEU = (46, 204, 113)
COR_PAINEL = (37, 52, 68)

# --- Layout ---
LARGURA, ALTURA = 900, 540
TAMANHO_CELULA = 130
GAP = 8
ORIGEM_TABULEIRO = (40, 60)
ORIGEM_PAINEL = (480, 40)


@dataclass
class EstadoAnimacao:
    estado_atual: tuple[int, ...]
    indice_movimento: int
    pausado: bool
    resolveu_visivel: bool


def _desenhar_tabuleiro(superficie, estado: tuple[int, ...], origem: tuple[int, int], fonte) -> None:
    ox, oy = origem
    for idx, valor in enumerate(estado):
        linha, coluna = divmod(idx, 3)
        x = ox + coluna * (TAMANHO_CELULA + GAP)
        y = oy + linha * (TAMANHO_CELULA + GAP)
        rect = pygame.Rect(x, y, TAMANHO_CELULA, TAMANHO_CELULA)
        if valor == 0:
            pygame.draw.rect(superficie, COR_VAZIO, rect, border_radius=8)
        else:
            pygame.draw.rect(superficie, COR_PECA, rect, border_radius=8)
            pygame.draw.rect(superficie, COR_BORDA, rect, width=2, border_radius=8)
            texto = fonte.render(str(valor), True, COR_TEXTO)
            tr = texto.get_rect(center=rect.center)
            superficie.blit(texto, tr)


def _desenhar_painel(
    superficie,
    fontes,
    *,
    estado_inicial: tuple[int, ...],
    indice: int,
    total: int,
    melhor_fitness: float,
    caso_nome: str,
    resolveu_run: bool,
    pausado: bool,
    mostrar_resolveu: bool,
) -> None:
    fonte_titulo, fonte_label, fonte_pequena = fontes
    px, py = ORIGEM_PAINEL
    superficie.blit(fonte_titulo.render(f"Caso: {caso_nome}", True, COR_TEXTO), (px, py))

    linhas = [
        f"Movimento: {indice} / {total}",
        f"Fitness:   {melhor_fitness:.1f}",
        f"Resolveu (run): {'sim' if resolveu_run else 'nao'}",
    ]
    if not mostrar_resolveu:
        linhas.append(f"Estado:    {'PAUSADO' if pausado else 'rodando'}")
    for i, linha in enumerate(linhas):
        superficie.blit(fonte_label.render(linha, True, COR_TEXTO), (px, py + 40 + i * 28))

    if mostrar_resolveu:
        texto = fonte_titulo.render("RESOLVEU!", True, COR_RESOLVEU)
        superficie.blit(texto, (px, py + 40 + len(linhas) * 28))

    py_ref = py + 180
    superficie.blit(fonte_label.render("Inicial:", True, COR_TEXTO_FRACO), (px, py_ref))
    superficie.blit(
        fonte_pequena.render(str(estado_inicial), True, COR_TEXTO_FRACO),
        (px, py_ref + 24),
    )
    superficie.blit(fonte_label.render("Objetivo:", True, COR_TEXTO_FRACO), (px, py_ref + 56))
    superficie.blit(
        fonte_pequena.render(str(GOAL), True, COR_TEXTO_FRACO),
        (px, py_ref + 80),
    )

    superficie.blit(
        fonte_pequena.render("SPACE: pausa  R: reinicia  ESC: sai", True, COR_TEXTO_FRACO),
        (px, ALTURA - 30),
    )


def renderizar_frame_em_arquivo(
    output_path: Path,
    *,
    estado: tuple[int, ...],
    estado_inicial: tuple[int, ...],
    indice_movimento: int,
    total_movimentos: int,
    melhor_fitness: float,
    caso_nome: str,
    resolveu_run: bool,
    mostrar_resolveu: bool = False,
) -> None:
    """Renderiza um único frame e salva como PNG. Não abre janela.

    Útil para gerar screenshots em ambientes headless (set SDL_VIDEODRIVER=dummy
    no ambiente antes de chamar).
    """
    pygame.init()
    # Surface offscreen — não precisa de display.set_mode
    tela = pygame.Surface((LARGURA, ALTURA))
    fonte_titulo = pygame.font.SysFont(None, 36)
    fonte_label = pygame.font.SysFont(None, 24)
    fonte_pequena = pygame.font.SysFont(None, 20)
    fonte_peca = pygame.font.SysFont(None, 64, bold=True)

    tela.fill(COR_FUNDO)
    painel_rect = pygame.Rect(ORIGEM_PAINEL[0] - 20, ORIGEM_PAINEL[1] - 20, 400, ALTURA - 40)
    pygame.draw.rect(tela, COR_PAINEL, painel_rect, border_radius=10)

    _desenhar_tabuleiro(tela, estado, ORIGEM_TABULEIRO, fonte_peca)
    _desenhar_painel(
        tela,
        (fonte_titulo, fonte_label, fonte_pequena),
        estado_inicial=estado_inicial,
        indice=indice_movimento,
        total=total_movimentos,
        melhor_fitness=melhor_fitness,
        caso_nome=caso_nome,
        resolveu_run=resolveu_run,
        pausado=False,
        mostrar_resolveu=mostrar_resolveu,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pygame.image.save(tela, str(output_path))
    pygame.quit()


def animar(json_path: Path, delay_ms: int = 300) -> None:
    """Abre janela Pygame e anima a solução do JSON indicado."""
    dados = carregar_detalhe_json(json_path)
    estado_inicial = parse_estado_inicial(dados["estado_inicial"])
    movimentos = mapear_direcoes(dados.get("movimentos_decodificados", []))
    melhor_fitness = float(dados.get("melhor_fitness", 0.0))
    caso_nome = str(dados.get("caso_nome", "?"))
    resolveu_run = bool(dados.get("resolveu", False))

    pygame.init()
    tela = pygame.display.set_mode((LARGURA, ALTURA))
    pygame.display.set_caption(f"8-Puzzle AG — {json_path.name}")
    fonte_titulo = pygame.font.SysFont(None, 36)
    fonte_label = pygame.font.SysFont(None, 24)
    fonte_pequena = pygame.font.SysFont(None, 20)
    fonte_peca = pygame.font.SysFont(None, 64, bold=True)

    estado_anim = EstadoAnimacao(
        estado_atual=estado_inicial,
        indice_movimento=0,
        pausado=False,
        resolveu_visivel=False,
    )

    relogio = pygame.time.Clock()
    ultimo_passo_ms = 0
    rodando = True
    while rodando:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                rodando = False
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    rodando = False
                elif evento.key == pygame.K_SPACE:
                    estado_anim.pausado = not estado_anim.pausado
                elif evento.key == pygame.K_r:
                    estado_anim.estado_atual = estado_inicial
                    estado_anim.indice_movimento = 0
                    estado_anim.resolveu_visivel = False

        agora = pygame.time.get_ticks()
        if (
            not estado_anim.pausado
            and estado_anim.indice_movimento < len(movimentos)
            and agora - ultimo_passo_ms >= delay_ms
        ):
            direcao = movimentos[estado_anim.indice_movimento]
            estado_anim.estado_atual = aplicar_movimento(estado_anim.estado_atual, direcao)
            estado_anim.indice_movimento += 1
            ultimo_passo_ms = agora
            if estado_anim.estado_atual == GOAL:
                estado_anim.resolveu_visivel = True

        tela.fill(COR_FUNDO)
        painel_rect = pygame.Rect(ORIGEM_PAINEL[0] - 20, ORIGEM_PAINEL[1] - 20, 400, ALTURA - 40)
        pygame.draw.rect(tela, COR_PAINEL, painel_rect, border_radius=10)

        _desenhar_tabuleiro(tela, estado_anim.estado_atual, ORIGEM_TABULEIRO, fonte_peca)
        _desenhar_painel(
            tela,
            (fonte_titulo, fonte_label, fonte_pequena),
            estado_inicial=estado_inicial,
            indice=estado_anim.indice_movimento,
            total=len(movimentos),
            melhor_fitness=melhor_fitness,
            caso_nome=caso_nome,
            resolveu_run=resolveu_run,
            pausado=estado_anim.pausado,
            mostrar_resolveu=estado_anim.resolveu_visivel,
        )

        pygame.display.flip()
        relogio.tick(60)

    pygame.quit()
