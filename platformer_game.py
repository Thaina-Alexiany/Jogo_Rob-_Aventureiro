import pgzrun
import random
import math
import threading
import pygame
from pgzero.rect import Rect

# --- CONFIGURAÇÕES ---
WIDTH = 800
HEIGHT = 400
CHAO_Y = 350

# --- VARIÁVEIS ---
velocidade = 7
gravidade = 1
pulo_forca = -18

pontos = 0
fase = 1
vidas = 3

estado_jogo = "menu"  # menu, playing, game_over
mensagem = ""
musica_ligada = True

# --- ROBÔ ---
robo = Rect((80, CHAO_Y - 60), (40, 60))
robo_vy = 0
pulando = False
robo_passo = 0
robo_antena_brilho = True

# --- OBSTÁCULOS ---
obstaculos = [Rect((800, CHAO_Y - 40), (40, 40))]

# --- INIMIGOS ---
inimigos = [Rect((900, CHAO_Y - 50), (40, 50))]
inimigos_dir = [2]

# --- SONS ---
pygame.mixer.init(frequency=44100, size=-16, channels=2)

def gerar_som(freq, duracao=0.2, volume=0.5):
    amostragem = 44100
    n = int(amostragem * duracao)
    buffer = bytearray()
    for i in range(n):
        valor = int(volume * 32767 * math.sin(2 * math.pi * freq * i / amostragem))
        buffer += int(valor).to_bytes(2, byteorder="little", signed=True)
    try:
        return pygame.mixer.Sound(buffer=bytes(buffer))
    except Exception:
        return None

som_pulo = gerar_som(700, 0.18)
som_colisao = gerar_som(150, 0.4)
som_fase = gerar_som(300, 0.15)

def tocar_som_async(som):
    if not musica_ligada or som is None:
        return
    threading.Thread(target=som.play, daemon=True).start()

# --- MUSICA DE FUNDO SIMPLES ---
notas = [261, 293, 329, 349, 392, 440, 392, 349]
musica_index = 0

def tocar_musica():
    global musica_index
    if estado_jogo != "playing" or not musica_ligada:
        return
    freq = notas[musica_index % len(notas)]
    som = gerar_som(freq, 0.15, 0.15)
    tocar_som_async(som)
    musica_index += 1
    clock.schedule_unique(tocar_musica, 0.2)

# --- FUNÇÕES AUXILIARES ---
def resetar_posicao_e_obstaculos_e_inimigos():
    global robo, robo_vy, pulando, obstaculos, inimigos, inimigos_dir
    robo.x, robo.y = 80, CHAO_Y - 60
    robo_vy = 0
    pulando = False

    # Obstáculos iniciais mais próximos para primeira fase mais rápida
    obstaculos[:] = [Rect((800, CHAO_Y - random.randint(30, 80)), (40, random.randint(30, 80)))]
    inimigos[:] = [Rect((900, CHAO_Y - 50), (40, 50))]
    inimigos_dir[:] = [1]

def mostrar_mensagem(texto, tempo=2.0):
    """Mostra uma mensagem temporária que desaparece após 'tempo' segundos."""
    global mensagem
    mensagem = texto
    clock.schedule_unique(limpar_mensagem, tempo)

def limpar_mensagem():
    global mensagem
    mensagem = ""

# --- DESENHO ---
def desenhar_robo():
    global robo_passo, robo_antena_brilho
    screen.draw.filled_rect(robo, (100, 200, 255))
    cabeca = Rect(robo.x + 5, robo.y - 30, 30, 30)
    screen.draw.filled_rect(cabeca, (80, 180, 255))
    screen.draw.filled_circle((cabeca.x + 10, cabeca.y + 10), 4, (255, 255, 255))
    screen.draw.filled_circle((cabeca.x + 20, cabeca.y + 10), 4, (255, 255, 255))
    screen.draw.filled_circle((cabeca.x + 10, cabeca.y + 10), 2, (0, 0, 0))
    screen.draw.filled_circle((cabeca.x + 20, cabeca.y + 10), 2, (0, 0, 0))
    if robo_antena_brilho:
        screen.draw.line((cabeca.x + 15, cabeca.y), (cabeca.x + 15, cabeca.y - 15), (255, 0, 0))
        screen.draw.filled_circle((cabeca.x + 15, cabeca.y - 15), 3, (255, 0, 0))
    screen.draw.line((robo.x, robo.y + 20), (robo.x - 15, robo.y + 30), (150, 150, 150))
    screen.draw.line((robo.x + 40, robo.y + 20), (robo.x + 55, robo.y + 30), (150, 150, 150))
    desloc = 3 if robo_passo % 20 < 10 else -3
    screen.draw.line((robo.x + 10, robo.bottom), (robo.x + 10, robo.bottom + 15 + desloc), (80, 80, 80))
    screen.draw.line((robo.x + 30, robo.bottom), (robo.x + 30, robo.bottom + 15 - desloc), (80, 80, 80))
    robo_passo += 1
    if robo_passo >= 40:
        robo_passo = 0
    if robo_passo % 10 == 0:
        robo_antena_brilho = not robo_antena_brilho

# --- BOTÕES ---
botao_comecar = Rect((WIDTH//2-100, 200, 200, 50))
botao_musica = Rect((WIDTH//2-100, 270, 200, 50))
botao_sair = Rect((WIDTH//2-100, 340, 200, 50))

def draw():
    cor_ceu = (10, 10, 30 + min(100, fase*5))
    cor_chao = (50, max(60, 180 - fase*5), 50)
    screen.fill(cor_ceu)
    screen.draw.filled_rect(Rect((0, CHAO_Y, WIDTH, 50)), cor_chao)

    if estado_jogo == "menu":
        screen.draw.text("ROBÔ AVENTUREIRO", center=(WIDTH//2, 120), fontsize=56, color="white")
        screen.draw.filled_rect(botao_comecar, "green")
        screen.draw.text("Começar Jogo", center=botao_comecar.center, fontsize=32, color="white")
        screen.draw.filled_rect(botao_musica, "blue")
        screen.draw.text(f"Música {'ON' if musica_ligada else 'OFF'}", center=botao_musica.center, fontsize=28, color="white")
        screen.draw.filled_rect(botao_sair, "red")
        screen.draw.text("Sair", center=botao_sair.center, fontsize=28, color="white")
        return

    if estado_jogo == "game_over":
        desenhar_robo()
        screen.draw.textbox("GAME OVER", Rect((WIDTH//2-200, HEIGHT//2-60, 400, 80)), color="red", background="black")
        screen.draw.text("Pressione R para reiniciar", center=(WIDTH//2, HEIGHT//2 + 40), fontsize=28, color="white")
        return

    # JOGO
    desenhar_robo()
    for o in obstaculos:
        screen.draw.filled_rect(o, (200, 50 + min(200, fase*10), 50))
    for i in inimigos:
        screen.draw.filled_rect(i, (255, 0, 0))
    screen.draw.text(f"Pontos: {pontos}", (10, 10), fontsize=28, color="white")
    screen.draw.text(f"Fase: {fase}", (10, 40), fontsize=24, color="white")
    screen.draw.text(f"Vidas: {vidas}", (10, 70), fontsize=24, color="red")
    if mensagem:
        screen.draw.textbox(mensagem, Rect((WIDTH//2-220, 120, 440, 80)), color="white", background="black")

# --- LÓGICA ---
def atualizar_robo():
    global robo_vy, pulando
    robo_vy += gravidade
    robo.y += robo_vy
    if robo.bottom >= CHAO_Y:
        robo.bottom = CHAO_Y
        robo_vy = 0
        pulando = False

def atualizar_obstaculos_e_inimigos():
    global pontos, fase, velocidade, mensagem, vidas, estado_jogo

    for o in list(obstaculos):
        o.x -= velocidade
        if o.right < 0:
            obstaculos.remove(o)
            altura = random.randint(30, 80)
            # Distância menor para primeira fase, aumenta com o avanço
            distancia_min = max(180 - fase*10, 120)
            distancia_max = max(350 - fase*10, 180)
            obstaculos.append(Rect((random.randint(WIDTH + distancia_min, WIDTH + distancia_max), CHAO_Y - altura), (40, altura)))
            pontos += 1
            tocar_som_async(som_fase)
            if pontos % 10 == 0:
                fase += 1
                velocidade += 0.6
                mostrar_mensagem(f"Parabéns! Fase {fase} concluída!", tempo=2.0)

        if robo.colliderect(o):
            vidas -= 1
            tocar_som_async(som_colisao)
            if vidas > 0:
                mostrar_mensagem(f"Você perdeu uma vida! Restam {vidas}", tempo=2.0)
                resetar_posicao_e_obstaculos_e_inimigos()
            else:
                mostrar_mensagem("Game Over! Você perdeu todas as vidas.", tempo=2.0)
                estado_jogo = "game_over"

    for idx, i in enumerate(inimigos):
        i.x += (velocidade - 1 + fase*0.3) * (1 if inimigos_dir[idx] > 0 else -1)
        if i.left < 500 or i.right > WIDTH:
            inimigos_dir[idx] *= -1
        if robo.colliderect(i):
            vidas -= 1
            tocar_som_async(som_colisao)
            if vidas > 0:
                mostrar_mensagem(f"Você bateu no inimigo! Restam {vidas}", tempo=2.0)
                resetar_posicao_e_obstaculos_e_inimigos()
            else:
                mostrar_mensagem("Game Over! Você perdeu todas as vidas.", tempo=2.0)
                estado_jogo = "game_over"

# --- UPDATE & INPUT ---
def update():
    if estado_jogo == "playing":
        atualizar_robo()
        atualizar_obstaculos_e_inimigos()

def on_key_down(key):
    global robo_vy, pulando, estado_jogo, pontos, fase, vidas, velocidade, mensagem
    if estado_jogo == "playing" and key == keys.SPACE and not pulando:
        robo_vy = pulo_forca
        pulando = True
        tocar_som_async(som_pulo)
    elif estado_jogo == "game_over" and key == keys.R:
        estado_jogo = "menu"
        pontos = 0
        fase = 1
        vidas = 3
        velocidade = 6
        mensagem = ""
        resetar_posicao_e_obstaculos_e_inimigos()

def on_mouse_down(pos):
    global estado_jogo, musica_ligada
    if estado_jogo == "menu":
        if botao_comecar.collidepoint(pos):
            estado_jogo = "playing"
            pontos = 0
            fase = 1
            vidas = 3
            velocidade = 6
            mensagem = ""
            resetar_posicao_e_obstaculos_e_inimigos()
            tocar_musica()
        elif botao_musica.collidepoint(pos):
            musica_ligada = not musica_ligada
        elif botao_sair.collidepoint(pos):
            exit()

# --- INICIALIZAÇÃO ---
resetar_posicao_e_obstaculos_e_inimigos()
pgzrun.go()
