# ==========================================
# ЧАСТЬ 1: ИНИЦИАЛИЗАЦИЯ И РЕТРО-ЗВУКИ
# ==========================================
import pygame
import sys
import random
import math

# Инициализация Pygame
pygame.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Mario Bros. 1983 - Slipice Phase (Ice Edition)")
clock = pygame.time.Clock()

# Цвета оригинального игрового автомата
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 168, 0)
BRIGHT_GREEN = (0, 252, 0)
BLUE = (0, 112, 236)
SKY_BLUE = (60, 188, 252)
RED = (228, 0, 0)
MARIO_SKIN = (252, 188, 176)
MARIO_BLUE = (0, 0, 168)
GOLD = (252, 228, 0)

# ГЕОМЕТРИЯ ПЛАТФОРМ ОРИГИНАЛЬНОГО ЭКРАНА 1983 ГОДА
PLATFORMS = [
    pygame.Rect(0, 560, 800, 40),      # Пол
    pygame.Rect(0, 440, 240, 20),      # Нижний левый ярус
    pygame.Rect(560, 440, 240, 20),    # Нижний правый ярус
    pygame.Rect(160, 320, 480, 20),    # Средний длинный этаж
    pygame.Rect(0, 200, 200, 20),      # Верхний левый ярус
    pygame.Rect(600, 200, 200, 20),    # Верхний правый ярус
]

pow_block = pygame.Rect(360, 440, 80, 30)
pow_uses = 3
frozen_platforms = [] # Список платформ, которые заморозит Слипайс

# ЗВУКОВОЙ СИНТЕЗАТОР (Чистый Python без numpy)
pygame.mixer.init(frequency=22050, size=-8, channels=1)

def generate_clean_sound(sound_type, duration=0.2):
    sample_rate = 22050
    total_samples = int(sample_rate * duration)
    sound_bytes = bytearray(total_samples)
    
    for t in range(total_samples):
        progress = t / total_samples
        if sound_type == "jump":
            freq = 200 + progress * 600
            val = math.sin(2 * math.pi * freq * (t / sample_rate))
            sample = int((val + 1) * 127)
        elif sound_type == "hit":
            freq = 80 * (1.0 - progress)
            val = math.sin(2 * math.pi * freq * (t / sample_rate)) * ((t * 997) % 10 / 10)
            sample = int((val + 1) * 127)
        elif sound_type == "kick":
            freq = 600 - progress * 400
            val = math.sin(2 * math.pi * freq * (t / sample_rate))
            sample = int((val + 1) * 127)
            
        sound_bytes[t] = max(0, min(255, sample))
    return pygame.mixer.Sound(buffer=sound_bytes)

sound_jump = generate_clean_sound("jump", duration=0.15)
sound_hit = generate_clean_sound("hit", duration=0.2)
sound_kick = generate_clean_sound("kick", duration=0.12)
# ==========================================
# ЧАСТЬ 2: КЛАСС ИГРОКА (МАРИО) С ФИЗИКОЙ ЛЬДА
# ==========================================
class Player:
    def __init__(self):
        self.rect = pygame.Rect(400, 500, 30, 42)
        self.vx = 0
        self.vy = 0
        self.speed = 5
        self.gravity = 0.6
        self.on_ground = False
        self.facing_right = True

    def update(self):
        keys = pygame.key.get_pressed()
        target_vx = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            target_vx = -self.speed
            self.facing_right = False
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            target_vx = self.speed
            self.facing_right = True

        # ПРОВЕРКА: Стоит ли Марио на обледеневшей платформе?
        player_on_ice = False
        under_player = pygame.Rect(self.rect.x, self.rect.bottom + 1, self.rect.width, 2)
        for fp in frozen_platforms:
            if under_player.colliderect(fp):
                player_on_ice = True

        if player_on_ice:
            # Марио плавно скользит с заносами на льду
            self.vx += (target_vx - self.vx) * 0.06
        else:
            # Четкое мгновенное торможение на обычной платформе
            self.vx = target_vx

        # Прыжок
        if (keys[pygame.K_SPACE] or keys[pygame.K_w] or keys[pygame.K_UP]) and self.on_ground:
            self.vy = -14
            self.on_ground = False
            sound_jump.play()

        self.vy += self.gravity
        if self.vy > 10: self.vy = 10

        # Движение по X и фича сквозных боковых экранов
        self.rect.x += int(self.vx)
        if self.rect.right < 0: self.rect.left = SCREEN_WIDTH
        if self.rect.left > SCREEN_WIDTH: self.rect.right = 0

        self.rect.y += self.vy
        self.on_ground = False
        
        if self.rect.colliderect(pow_block) and self.vy > 0 and self.rect.bottom <= pow_block.top + 10:
            self.rect.bottom = pow_block.top
            self.vy = 0
            self.on_ground = True

        for p in PLATFORMS:
            if self.rect.colliderect(p):
                if self.vy > 0 and self.rect.bottom <= p.top + 10:
                    self.rect.bottom = p.top
                    self.vy = 0
                    self.on_ground = True
                elif self.vy < 0 and self.rect.top >= p.bottom - 10:
                    self.rect.top = p.bottom
                    self.vy = 0
                    sound_hit.play()
                    check_headbutt(p)

        if self.rect.colliderect(pow_block) and self.vy < 0 and self.rect.top >= pow_block.bottom - 10:
            self.rect.top = pow_block.bottom
            self.vy = 0
            sound_hit.play()
            trigger_pow()

    def draw(self, surface):
        # Геометрия Марио
        pygame.draw.rect(surface, MARIO_BLUE, (self.rect.x + 4, self.rect.y + 16, 22, 26))
        pygame.draw.rect(surface, (100, 50, 0), (self.rect.x + 3, self.rect.y + 36, 10, 6))
        pygame.draw.rect(surface, (100, 50, 0), (self.rect.x + 17, self.rect.y + 36, 10, 6))
        pygame.draw.rect(surface, RED, (self.rect.x + 6, self.rect.y + 16, 18, 10))
        pygame.draw.circle(surface, MARIO_SKIN, (self.rect.x + 15, self.rect.y + 10), 9)
        pygame.draw.rect(surface, RED, (self.rect.x + 6, self.rect.y, 18, 5))
        if self.facing_right:
            pygame.draw.rect(surface, RED, (self.rect.x + 12, self.rect.y + 2, 16, 3))
            pygame.draw.rect(surface, BLACK, (self.rect.x + 19, self.rect.y + 7, 3, 4))
        else:
            pygame.draw.rect(surface, RED, (self.rect.x + 2, self.rect.y + 2, 16, 3))
            pygame.draw.rect(surface, BLACK, (self.rect.x + 8, self.rect.y + 7, 3, 4))
# ==========================================
# ЧАСТЬ 3: БЕСТИАРИЙ, ЛОГИКА СЛИПАЙСА И ЗАПУСК
# ==========================================
class Enemy:
    def __init__(self, enemy_type):
        self.enemy_type = enemy_type  # 'turtle', 'crab', 'fly', 'slipice'
        spawn_x = random.choice([40, 720])
        self.rect = pygame.Rect(spawn_x, 150, 30, 30)
        
        if self.enemy_type == 'turtle': self.speed = 2
        elif self.enemy_type == 'crab': self.speed = 1.5
        elif self.enemy_type == 'fly': self.speed = 2.5
        elif self.enemy_type == 'slipice': self.speed = 1.8 
            
        self.vx = self.speed if self.rect.x < 400 else -self.speed
        self.vy = 0
        self.is_flipped = False
        self.flip_timer = 0
        self.is_angry = False
        self.fly_jump_timer = 0
        self.fly_is_jumping = False

    def update(self):
        if not self.is_flipped:
            if self.enemy_type == 'slipice':
                self.rect.x += self.vx
                # Ледышка бежит к середине средних платформ и превращает их в ЛЁД!
                if 280 < self.rect.x < 520 and self.vy == 0:
                    for p in PLATFORMS:
                        if p.collidepoint(self.rect.centerx, self.rect.bottom + 2):
                            if p not in frozen_platforms:
                                frozen_platforms.append(p)
                    self.rect.y = 9999 # Убираем растаявшую ледышку
            elif self.enemy_type == 'fly':
                self.fly_jump_timer += 1
                if not self.fly_is_jumping and self.vy == 0:
                    if self.fly_jump_timer > 60: # 1 секунда паузы перед прыжком
                        self.vy = -8
                        self.fly_is_jumping = True
                        self.fly_jump_timer = 0
                if self.vy != 0:
                    self.rect.x += self.vx
            else:
                self.rect.x += self.vx

            if self.rect.right < 0: self.rect.left = SCREEN_WIDTH
            if self.rect.left > SCREEN_WIDTH: self.rect.right = 0
        else:
            self.flip_timer -= 1
            if self.flip_timer <= 0:
                self.is_flipped = False
                if self.enemy_type == 'crab' and not self.is_angry:
                    self.is_angry = True; self.speed = 3.5
                    self.vx = self.speed if self.vx > 0 else -self.speed

        self.vy += 0.5
        if self.vy > 10: self.vy = 10
        self.rect.y += self.vy

        for p in PLATFORMS:
            if self.rect.colliderect(p) and self.vy > 0 and self.rect.bottom <= p.top + 10:
                self.rect.bottom = p.top; self.vy = 0
                if self.enemy_type == 'fly': self.fly_is_jumping = False

    def draw(self, surface):
        if self.is_flipped:
            pygame.draw.rect(surface, SKY_BLUE, self.rect, border_radius=5)
            pygame.draw.line(surface, WHITE, (self.rect.x+6, self.rect.y+10), (self.rect.x+12, self.rect.y+16), 2)
        else:
            if self.enemy_type == 'turtle':
                pygame.draw.circle(surface, GOLD, (self.rect.x+16, self.rect.y+20), 12)
                pygame.draw.ellipse(surface, GREEN, (self.rect.x+4, self.rect.y+4, 24, 18))
            elif self.enemy_type == 'crab':
                color = RED if self.is_angry else (160, 32, 240)
                pygame.draw.rect(surface, color, (self.rect.x+4, self.rect.y+10, 24, 16), border_radius=4)
            elif self.enemy_type == 'fly':
                pygame.draw.ellipse(surface, WHITE, (self.rect.x+2, self.rect.y+6, 14, 12))
                pygame.draw.circle(surface, (255, 105, 180), (self.rect.x+16, self.rect.y+18), 10)
            elif self.enemy_type == 'slipice':
                pygame.draw.rect(surface, (0, 200, 255), self.rect, border_radius=4)
                pygame.draw.rect(surface, WHITE, self.rect, 2, border_radius=4)
                pygame.draw.circle(surface, WHITE, (self.rect.x+9, self.rect.y+10), 2)
                pygame.draw.circle(surface, WHITE, (self.rect.x+21, self.rect.y+10), 2)

def check_headbutt(platform_hit):
    for enemy in enemies:
        if enemy.rect.bottom == platform_hit.top:
            if platform_hit.left <= enemy.rect.centerx <= platform_hit.right:
                if enemy.enemy_type == 'crab' and not enemy.is_angry and not enemy.is_flipped:
                    enemy.is_angry = True; enemy.speed = 3.5
                    enemy.vx = enemy.speed if enemy.vx > 0 else -enemy.speed
                    enemy.vy = -5
                else:
                    enemy.is_flipped = True; enemy.flip_timer = 300

def trigger_pow():
    global pow_uses
    if pow_uses > 0:
        pow_uses -= 1
        for enemy in enemies:
            if enemy.vy == 0 and not enemy.is_flipped:
                if enemy.enemy_type == 'crab' and not enemy.is_angry:
                    enemy.is_angry = True; enemy.speed = 3.5
                    enemy.vx = enemy.speed if enemy.vx > 0 else -enemy.speed
                else:
                    enemy.is_flipped = True; enemy.flip_timer = 300

# Создание объектов
player = Player()
types = ['turtle', 'crab', 'fly', 'slipice']
enemies = [Enemy(random.choice(types)) for _ in range(4)]
score = 0
frame_count = 0

# ГЛАВНЫЙ ИГРОВОЙ ЦИКЛ
running = True
while running:
    clock.tick(60)
    frame_count += 1

    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False

    player.update()
    
    for enemy in list(enemies):
        enemy.update()

        # Респавн взамен растаявшего Слипайса
        if enemy.rect.y > SCREEN_HEIGHT + 20:
            enemies.remove(enemy)
            enemies.append(Enemy(random.choice(types)))

        # Столкновение Марио с врагом
        if player.rect.colliderect(enemy.rect):
            if enemy.is_flipped:
                sound_kick.play()
                enemies.remove(enemy)
                score += 100
                enemies.append(Enemy(random.choice(types)))
            else:
                player.rect.x, player.rect.y = 400, 500
                player.vx = 0; player.vy = 0
                frozen_platforms.clear() # При смерти лёд тает

    # --- РЕНДЕРИНГ ЭКРАНА ---
    screen.fill(BLACK) # Чистый темный фон канализации без факелов!

    # Отрисовка зеленых труб спавна
    pygame.draw.rect(screen, GREEN, (0, 140, 60, 60))
    pygame.draw.rect(screen, BRIGHT_GREEN, (0, 140, 60, 60), 3)
    pygame.draw.rect(screen, GREEN, (740, 140, 60, 60))
    pygame.draw.rect(screen, BRIGHT_GREEN, (740, 140, 60, 60), 3)

    # Отрисовка платформ (Синие или Замороженные Слипайсом)
    for p in PLATFORMS:
        if p in frozen_platforms:
            pygame.draw.rect(screen, (160, 240, 255), p)
            pygame.draw.rect(screen, WHITE, p, 2)
        else:
            pygame.draw.rect(screen, BLUE, p)
            pygame.draw.rect(screen, SKY_BLUE, p, 2)
            for step in range(p.left, p.right, 20):
                pygame.draw.line(screen, SKY_BLUE, (step, p.top), (step, p.bottom), 1)

    # Красный блок POW по центру
    if pow_uses > 0:
        pygame.draw.rect(screen, RED, pow_block, border_radius=4)
        pygame.draw.rect(screen, WHITE, pow_block, 2)
        font = pygame.font.SysFont("Arial", 18, bold=True)
        text = font.render("POW", True, WHITE)
        screen.blit(text, (pow_block.x + 20, pow_block.y + 5))

    # Вывод персонажей
    player.draw(screen)
    for enemy in enemies: enemy.draw(screen)

    # Текст интерфейса
    font = pygame.font.SysFont("Courier New", 28, bold=True)
    score_text = font.render(f"MARIO {score:06d}", True, WHITE)
    screen.blit(score_text, (20, 20))
    for i in range(pow_uses): pygame.draw.circle(screen, RED, (420 + i*20, 25), 6)

    pygame.display.flip()

pygame.quit()
sys.exit()


# --- СКРИПТ ДЛЯ СОЗДАНИЯ СВОЙСТВ ПРОДУКТА MARIO.PY ---
import os

metadata_content = """
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        '040904b0',
        [StringProperty('CompanyName', 'Gleb & Besya Hacking Corp.'),
        StringProperty('FileDescription', 'Mario Game'),
        StringProperty('FileVersion', '1.0.0'),
        StringProperty('InternalName', 'mario'),
        StringProperty('LegalCopyright', 'Copyright (c) 2026 Gleb.'),
        StringProperty('OriginalFilename', 'mario.exe'),
        StringProperty('ProductName', 'Mario Bros. 1983 Special Edition'),
        StringProperty('ProductVersion', '1.0.0')])
      ]), 
    VarFileInfo([VarVersionInfo('Translation', [1033, 1200])])
  ]
)
"""

# Записываем свойства в текстовый файл конфигурации
with open("file_version_info.txt", "w", encoding="utf-8") as f:
    f.write(metadata_content.strip())
