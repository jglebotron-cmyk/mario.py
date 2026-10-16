# --- CODE FOR THE GAME ---
import pygame
import sys
import random
import math

# Инициализация звукового движка (22050 Гц, 8 бит, моно)
pygame.mixer.init(frequency=22050, size=-8, channels=1)

def generate_bytebeat_sound(formula_func, duration=0.2):
    """Generates 8‑bit sound using the Bytebeat mathematical formula."""
    sample_rate = 22050
    total_samples = int(sample_rate * duration)
    
    # Собираем байты по формуле для каждого момента времени t
    sound_bytes = bytearray(
        int(formula_func(t)) & 255 for t in range(total_samples)
    )
    
    # Превращаем байты в объект Sound для Pygame
    return pygame.mixer.Sound(buffer=sound_bytes)

# --- НАШИ РЕТРО-ФОРМУЛЫ ---

# 1. Звук прыжка (быстрое скольжение частоты вверх)
sound_jump = generate_bytebeat_sound(lambda t: (t * (3 + (t >> 8 & 3))) | (t >> 4), duration=0.15)

# 2. Звук удара головой/POW (классический низкий взрывной шум/скрежет)
sound_hit = generate_bytebeat_sound(lambda t: (t * 5 & t >> 7) | (t * 3 & t >> 10), duration=0.25)

# 3. Звук пинка врага (короткий аркадный «блип»)
sound_kick = generate_bytebeat_sound(lambda t: (t * (t >> 6 & 5)), duration=0.1)

# Размеры экрана (нужны для бесконечного экрана по бокам)
SCREEN_WIDTH = 800

# Цвета для отрисовки персонажей
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 168, 0)
BLUE = (0, 112, 236)
SKY_BLUE = (60, 188, 252)
RED = (228, 0, 0)
MARIO_SKIN = (252, 188, 176)
MARIO_BLUE = (0, 0, 168)
GOLD = (252, 228, 0)

class Player:
    def __init__(self):
        self.rect = pygame.Rect(400, 500, 30, 42)
        self.vx = 0
        self.vy = 0
        self.speed = 5
        self.gravity = 0.6
        self.on_ground = False
        self.facing_right = True

    def update(self, platforms, pow_block, trigger_pow_func, check_headbutt_func):
        keys = pygame.key.get_pressed()
        self.vx = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vx = -self.speed
            self.facing_right = False
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vx = self.speed
            self.facing_right = True

        if (keys[pygame.K_SPACE] or keys[pygame.K_w] or keys[pygame.K_UP]) and self.on_ground:
            self.vy = -14
            sound_jump.play()
            self.on_ground = False

        self.vy += self.gravity
        if self.vy > 10: self.vy = 10

        # Бесконечный экран по бокам
        self.rect.x += self.vx
        if self.rect.right < 0: self.rect.left = SCREEN_WIDTH
        if self.rect.left > SCREEN_WIDTH: self.rect.right = 0

        self.rect.y += self.vy
        self.on_ground = False
        
        # Столкновение с блоком POW сверху
        if pow_block and self.rect.colliderect(pow_block) and self.vy > 0 and self.rect.bottom <= pow_block.top + 10:
            self.rect.bottom = pow_block.top
            self.vy = 0
            self.on_ground = True

        # Столкновения с обычными платформами
        for p in platforms:
            if self.rect.colliderect(p):
                if self.vy > 0 and self.rect.bottom <= p.top + 10:
                    self.rect.bottom = p.top
                    self.vy = 0
                    self.on_ground = True
                elif self.vy < 0 and self.rect.top >= p.bottom - 10:
                    self.rect.top = p.bottom
                    self.vy = 0
                    sound_hit.play()
                    check_headbutt_func(p)

        # Проверка удара головой по блоку POW снизу
        if pow_block and self.rect.colliderect(pow_block) and self.vy < 0 and self.rect.top >= pow_block.bottom - 10:
            self.rect.top = pow_block.bottom
            self.vy = 0
            sound_hit.play()
            trigger_pow_func()

    def draw(self, surface):
        # Комбинезон
        pygame.draw.rect(surface, MARIO_BLUE, (self.rect.x + 4, self.rect.y + 16, 22, 26))
        # Ноги / Обувь
        pygame.draw.rect(surface, (100, 50, 0), (self.rect.x + 3, self.rect.y + 36, 10, 6))
        pygame.draw.rect(surface, (100, 50, 0), (self.rect.x + 17, self.rect.y + 36, 10, 6))
        # Рубашка
        pygame.draw.rect(surface, RED, (self.rect.x + 6, self.rect.y + 16, 18, 10))
        # Голова
        pygame.draw.circle(surface, MARIO_SKIN, (self.rect.x + 15, self.rect.y + 10), 9)
        # Кепка
        pygame.draw.rect(surface, RED, (self.rect.x + 6, self.rect.y, 18, 5))
        if self.facing_right:
            pygame.draw.rect(surface, RED, (self.rect.x + 12, self.rect.y + 2, 16, 3))
            pygame.draw.rect(surface, BLACK, (self.rect.x + 19, self.rect.y + 7, 3, 4))
        else:
            pygame.draw.rect(surface, RED, (self.rect.x + 2, self.rect.y + 2, 16, 3))
            pygame.draw.rect(surface, BLACK, (self.rect.x + 8, self.rect.y + 7, 3, 4))

class Enemy:
    def __init__(self, enemy_type):
        self.enemy_type = enemy_type  # 'turtle', 'crab', 'fly'
        # Случайный спавн слева или справа у верхних труб
        spawn_x = random.choice([20, 750])
        self.rect = pygame.Rect(spawn_x, 150, 32, 32)
        
        if self.enemy_type == 'turtle': self.speed = 2
        elif self.enemy_type == 'crab': self.speed = 1.5
        elif self.enemy_type == 'fly': self.speed = 2.5
            
        self.vx = self.speed if self.rect.x < 400 else -self.speed
        self.vy = 0
        self.is_flipped = False
        self.flip_timer = 0
        self.is_angry = False
        
        self.fly_jump_timer = 0
        self.fly_is_jumping = False

    def update(self, platforms):
        if not self.is_flipped:
            if self.enemy_type == 'fly':
                self.fly_jump_timer += 1
                if not self.fly_is_jumping and self.vy == 0:
                    if self.fly_jump_timer > 60:
                        self.vy = -8
                        self.fly_is_jumping = True
                        self.fly_jump_timer = 0
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
                    self.is_angry = True
                    self.speed = 3.5
                    self.vx = self.speed if self.vx > 0 else -self.speed

        self.vy += 0.5
        if self.vy > 10: self.vy = 10
        self.rect.y += self.vy

        for p in platforms:
            if self.rect.colliderect(p) and self.vy > 0 and self.rect.bottom <= p.top + 10:
                self.rect.bottom = p.top
                self.vy = 0
                if self.enemy_type == 'fly':
                    self.fly_is_jumping = False

    def draw(self, surface):
        if self.is_flipped:
            pygame.draw.rect(surface, SKY_BLUE, self.rect, border_radius=5)
            pygame.draw.line(surface, WHITE, (self.rect.x+6, self.rect.y+10), (self.rect.x+12, self.rect.y+16), 2)
            pygame.draw.line(surface, WHITE, (self.rect.x+26, self.rect.y+10), (self.rect.x+20, self.rect.y+16), 2)
        else:
            if self.enemy_type == 'turtle':
                pygame.draw.circle(surface, GOLD, (self.rect.x+16, self.rect.y+20), 12)
                pygame.draw.ellipse(surface, GREEN, (self.rect.x+4, self.rect.y+4, 24, 18))
            elif self.enemy_type == 'crab':
                color = RED if self.is_angry else (160, 32, 240)
                pygame.draw.rect(surface, color, (self.rect.x+4, self.rect.y+10, 24, 16), border_radius=4)
                pygame.draw.circle(surface, color, (self.rect.x+6, self.rect.y+6), 6)
                pygame.draw.circle(surface, color, (self.rect.x+26, self.rect.y+6), 6)
            elif self.enemy_type == 'fly':
                pygame.draw.ellipse(surface, WHITE, (self.rect.x+2, self.rect.y+6, 14, 12))
                pygame.draw.ellipse(surface, WHITE, (self.rect.x+16, self.rect.y+6, 14, 12))
                pygame.draw.circle(surface, (255, 105, 180), (self.rect.x+16, self.rect.y+18), 10)
# Инициализация
pygame.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Mario Bros. 1983 - Спец-издание")
clock = pygame.time.Clock()

# Цвета уровня
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 168, 0)
BRIGHT_GREEN = (0, 252, 0)
BLUE = (0, 112, 236)
SKY_BLUE = (60, 188, 252)
RED = (228, 0, 0)
GOLD = (252, 228, 0)

# Координаты факелов на фоне (исправлено!)
TORCH_X_POSITIONS = [150, 300, 500, 650]

# Геометрия уровней платформ
PLATFORMS = [
    pygame.Rect(0, 560, 800, 40),      # Пол
    pygame.Rect(0, 440, 240, 20),      # Нижний левый
    pygame.Rect(560, 440, 240, 20),    # Нижний правый
    pygame.Rect(160, 320, 480, 20),    # Средний ярус
    pygame.Rect(0, 200, 200, 20),      # Верхний левый
    pygame.Rect(600, 200, 200, 20),    # Верхний правый
]

pow_block = pygame.Rect(360, 440, 80, 30)
pow_uses = 3

# Типы врагов для случайного появления
ENEMY_TYPES = ['turtle', 'crab', 'fly']
enemies = []

def check_headbutt(platform_hit):
    for enemy in enemies:
        if enemy.rect.bottom == platform_hit.top:
            if platform_hit.left <= enemy.rect.centerx <= platform_hit.right:
                if enemy.enemy_type == 'crab' and not enemy.is_angry and not enemy.is_flipped:
                    enemy.is_angry = True
                    enemy.speed = 3.5
                    enemy.vx = enemy.speed if enemy.vx > 0 else -enemy.speed
                    enemy.vy = -5
                else:
                    enemy.is_flipped = True
                    enemy.flip_timer = 300

def trigger_pow():
    global pow_uses
    if pow_uses > 0:
        pow_uses -= 1
        for enemy in enemies:
            if enemy.vy == 0 and not enemy.is_flipped:
                if enemy.enemy_type == 'crab' and not enemy.is_angry:
                    enemy.is_angry = True
                    enemy.speed = 3.5
                    enemy.vx = enemy.speed if enemy.vx > 0 else -enemy.speed
                else:
                    enemy.is_flipped = True
                    enemy.flip_timer = 300

# Инициализация персонажей
player = Player()
for _ in range(4):
    enemies.append(Enemy(random.choice(ENEMY_TYPES)))

score = 0
frame_count = 0

# Основной цикл игры
running = True
while running:
    clock.tick(60)
    frame_count += 1

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Обновление логики (передаем функции ударов внутрь игрока)
    player.update(PLATFORMS, pow_block if pow_uses > 0 else None, trigger_pow, check_headbutt)
    
    for enemy in enemies:
        enemy.update(PLATFORMS)

        # Если Марио коснулся врага
        if player.rect.colliderect(enemy.rect):
            if enemy.is_flipped:
                enemies.remove(enemy)
                sound_kick.play()
                score += 200
                enemies.append(Enemy(random.choice(ENEMY_TYPES))) # Спавн нового взамен
            else:
                # Респавн Марио при гибели
                player.rect.x, player.rect.y = 400, 500
                player.vy = 0

    # --- ОТРИСОВКА ГРАФИКИ ---
    screen.fill(BLACK)

    # 1. Факелы на заднем плане (анимация мерцания огня)
    for fx in TORCH_X_POSITIONS:
        fire_size = 6 + math.sin(frame_count * 0.2) * 2
        pygame.draw.circle(screen, GOLD, (fx, 80), int(fire_size))
        pygame.draw.line(screen, WHITE, (fx, 80), (fx, 95), 2)

    # 2. Трубы, откуда лезут враги
    pygame.draw.rect(screen, GREEN, (0, 140, 60, 60))
    pygame.draw.rect(screen, BRIGHT_GREEN, (0, 140, 60, 60), 3)
    pygame.draw.rect(screen, GREEN, (740, 140, 60, 60))
    pygame.draw.rect(screen, BRIGHT_GREEN, (740, 140, 60, 60), 3)

    # 3. Текстурированные синие платформы с кирпичной насечкой
    for p in PLATFORMS:
        pygame.draw.rect(screen, BLUE, p)
        pygame.draw.rect(screen, SKY_BLUE, p, 2)
        for step in range(p.left, p.right, 20):
            pygame.draw.line(screen, SKY_BLUE, (step, p.top), (step, p.bottom), 1)

    # 4. Красный блок POW
    if pow_uses > 0:
        pygame.draw.rect(screen, RED, pow_block, border_radius=4)
        pygame.draw.rect(screen, WHITE, pow_block, 2)
        font = pygame.font.SysFont("Arial", 18, bold=True)
        text = font.render("POW", True, WHITE)
        screen.blit(text, (pow_block.x + 20, pow_block.y + 5))

    # 5. Рисуем Марио и монстров
    player.draw(screen)
    for enemy in enemies:
        enemy.draw(screen)

    # 6. Текст интерфейса (Счет)
    font = pygame.font.SysFont("Courier New", 28, bold=True)
    score_text = font.render(f"MARIO {score:06d}", True, WHITE)
    screen.blit(score_text, (20, 20))
    
    # Счётчик оставшихся зарядов POW точками
    for i in range(pow_uses):
        pygame.draw.circle(screen, RED, (420 + i*20, 25), 6)

    pygame.display.flip()

pygame.quit()
sys.exit()
