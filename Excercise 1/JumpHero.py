import os
import random
import math
import pygame
from os import listdir
from os.path import isfile, join
pygame.init()

jump_sound = pygame.mixer.Sound("assets/sounds/jump.mp3")
attack_sound = pygame.mixer.Sound("assets/sounds/sword.mp3")
damage_sound = pygame.mixer.Sound("assets/sounds/damage.mp3")
gameover_sound = pygame.mixer.Sound("assets/sounds/gameover.mp3")
win_sound = pygame.mixer.Sound("assets/sounds/win.mp3")
pygame.mixer.music.load("assets/sounds/background_music.mp3")  # Adjust the path as needed
pygame.mixer.music.set_volume(0.1)  # Set volume to 10% (very quiet)
pygame.mixer.music.play(-1, 0.0)  # Play music indefinitely


pygame.display.set_caption("Platformer")

WIDTH, HEIGHT = 1000, 800
FPS = 60
PLAYER_VEL = 5

window = pygame.display.set_mode((WIDTH, HEIGHT))


def flip(sprites):
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]


def load_sprite_sheets(dir1, dir2, width, height, direction=False):
    path = join("assets", dir1, dir2)
    images = [f for f in listdir(path) if isfile(join(path, f))]

    all_sprites = {}

    for image in images:
        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha()

        sprites = []
        for i in range(sprite_sheet.get_width() // width):
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(sprite_sheet, (0, 0), rect)
            sprites.append(pygame.transform.scale2x(surface))

        if direction:
            all_sprites[image.replace(".png", "") + "_right"] = sprites
            all_sprites[image.replace(".png", "") + "_left"] = flip(sprites)
        else:
            all_sprites[image.replace(".png", "")] = sprites

    return all_sprites


def get_block(size, blocktype):
    path = join("assets", "Terrain", "Terrain.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((size, size), pygame.SRCALPHA, 32)
    rect = pygame.Rect(blocktype, 0, size, size)
    surface.blit(image, (0, 0), rect)
    return pygame.transform.scale2x(surface)


class Player(pygame.sprite.Sprite):
    COLOR = (255, 0, 0)
    GRAVITY = 1
    SPRITES = load_sprite_sheets("char", "", 42, 42, True)
    ANIMATION_DELAY = 5

    def __init__(self, x, y, width, height, scale=1):
        super().__init__()
        self.rect = pygame.Rect(x, y, width*scale, height*scale)
        self.x_vel = 0
        self.y_vel = 0
        self.mask = None
        self.direction = "left"
        self.animation_count = 0
        self.fall_count = 0
        self.jump_count = 0
        self.hit = False
        self.hit_count = 0
        self.health = 3 # 💖 start with 3 lives
        self.won = False
        self.invincible = False
        self.invincibility_timer = 0
        self.attacking = False

    def jump(self):
        self.y_vel = -self.GRAVITY * 8
        self.animation_count = 0
        self.jump_count += 1
        if self.jump_count == 1:
            self.fall_count = 0

    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

    def make_hit(self):
        if not self.invincible:
            self.health -= 1
            self.hit = True
            self.invincible = True
            self.invincibility_timer = 60*3  # ~3 second at 60 FPS
            damage_sound.play()

    def attack(self):
        self.attacking = True

    def collect(self):
        self.won = True

    def move_left(self, vel):
        self.x_vel = -vel
        if self.direction != "left":
            self.direction = "left"
            self.animation_count = 0

    def move_right(self, vel):
        self.x_vel = vel
        if self.direction != "right":
            self.direction = "right"
            self.animation_count = 0

    def loop(self, fps):
        self.y_vel += min(1, (self.fall_count / fps) * self.GRAVITY)
        self.move(self.x_vel, self.y_vel)

        if self.hit:
            self.hit_count += 1
        if self.hit_count > fps * 2:
            self.hit = False
            self.hit_count = 0

        self.fall_count += 1
        self.update_sprite()

    def landed(self):
        self.fall_count = 0
        self.y_vel = 0
        self.jump_count = 0

    def hit_head(self):
        self.count = 0
        self.y_vel *= -1

    def update_sprite(self):
        sprite_sheet = "idle"
        if self.hit:
            sprite_sheet = "hit"
        elif self.y_vel < 0:
            if self.jump_count == 1:
                sprite_sheet = "jump"
            elif self.jump_count == 2:
                sprite_sheet = "double_jump"
        elif self.y_vel > self.GRAVITY * 2:
            sprite_sheet = "fall"
        elif self.x_vel != 0:
            sprite_sheet = "run"
        elif self.attacking == True:
            sprite_sheet = "attack"

        sprite_sheet_name = sprite_sheet + "_" + self.direction
        sprites = self.SPRITES[sprite_sheet_name]
        sprite_index = (self.animation_count //
                        self.ANIMATION_DELAY) % len(sprites)
        self.sprite = sprites[sprite_index]
        self.animation_count += 1
        self.update()

    def update(self):
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.sprite)
        if self.invincible:
            self.invincibility_timer -= 1
            if self.invincibility_timer <= 0:
                self.invincible = False


    def draw(self, win, offset_x):
        win.blit(self.sprite, (self.rect.x - offset_x, self.rect.y))

    def returnxpos(self):
        return self.rect.x 


class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, name=None):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.width = width
        self.height = height
        self.name = name

    def draw(self, win, offset_x):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y))


class Block(Object):
    def __init__(self, x, y, size, blocktype):
        super().__init__(x, y, size, size, blocktype)
        block = get_block(size, blocktype)
        self.image.blit(block, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)

class Apple(Object):
    ANIMATION_DELAY = 10

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, name="apple")
        self.sprites = load_sprite_sheets("Items", "Fruits", width, height)["Apple"]
        self.animation_count = 0
        self.image = self.sprites[0]
        self.mask = pygame.mask.from_surface(self.image)

    def loop(self):
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(self.sprites)
        self.image = self.sprites[sprite_index]
        self.animation_count += 1
        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)

class Fire(Object):
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "fire")
        self.fire = load_sprite_sheets("Traps", "Fire", width, height)
        self.image = self.fire["off"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "off"

    def on(self):
        self.animation_name = "on"

    def off(self):
        self.animation_name = "off"

    def loop(self):
        sprites = self.fire[self.animation_name]
        sprite_index = (self.animation_count //
                        self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1

        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)

        if self.animation_count // self.ANIMATION_DELAY > len(sprites):
            self.animation_count = 0


def get_background(name):
    image = pygame.image.load(join("assets", "Background", name))
    _, _, width, height = image.get_rect()
    tiles = []

    for i in range(WIDTH // width + 1):
        for j in range(HEIGHT // height + 1):
            pos = (i * width, j * height)
            tiles.append(pos)

    return tiles, image


def draw(window, background, bg_image, player, objects, offset_x):
    for tile in background:
        window.blit(bg_image, tile)

    for obj in objects:
        obj.draw(window, offset_x)

    player.draw(window, offset_x)

    draw_hearts(window, player.health) 

    pygame.display.update()


def handle_vertical_collision(player, objects, dy):
    collided_objects = []
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            if dy > 0:
                player.rect.bottom = obj.rect.top
                player.landed()
            elif dy < 0:
                player.rect.top = obj.rect.bottom
                player.hit_head()

            collided_objects.append(obj)

    return collided_objects


def collide(player, objects, dx):
    player.move(dx, 0)
    player.update()
    collided_object = None
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            collided_object = obj
            break

    player.move(-dx, 0)
    player.update()
    return collided_object


def handle_move(player, objects, offset_x):
    keys = pygame.key.get_pressed()

    player.x_vel = 0
    collide_left = collide(player, objects, -PLAYER_VEL * 2)
    collide_right = collide(player, objects, PLAYER_VEL * 2)

    x_mouse, y_mouse = pygame.mouse.get_pos()
    x_player = player.returnxpos()

    x_mouse = x_mouse - 30 + offset_x

    if x_mouse < x_player-3 and not collide_left:
        player.move_left(PLAYER_VEL)
    if x_mouse > x_player+3 and not collide_right:
        player.move_right(PLAYER_VEL)

    vertical_collide = handle_vertical_collision(player, objects, player.y_vel)
    to_check = [collide_left, collide_right, *vertical_collide]

    for obj in to_check:
        if obj and obj.name == "apple":
            player.collect()
        if obj and obj.name == "fire":
            player.make_hit()

def win_screen(window):
    run = True
    clock = pygame.time.Clock()
    pygame.mixer.music.pause()
    background, bg_image = get_background("8BitBackground.png")

    win_sound.play()

    while run:
        clock.tick(FPS)
        mouse_pos = pygame.mouse.get_pos()
        click = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                click = True

        # Draw the background
        for tile in background:
            window.blit(bg_image, tile)

        font = pygame.font.SysFont(None, 80)
        text_surf = font.render("You Won!", True, (80, 255, 80))
        text_rect = text_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 100))
        window.blit(text_surf, text_rect)

        if draw_button(window, "Restart", HEIGHT // 2 + 20, mouse_pos, click):
            run = False
            pygame.mixer.music.unpause()

        pygame.display.update()

def draw_button(win, text, y, mouse_pos, click):
    width, height = 300, 70
    x = WIDTH // 2 - width // 2
    button_rect = pygame.Rect(x, y, width, height)

    hovered = button_rect.collidepoint(mouse_pos)
    base_color = (50, 50, 200)
    hover_color = (70, 70, 255)
    color = hover_color if hovered else base_color

    pygame.draw.rect(win, color, button_rect, border_radius=12)
    pygame.draw.rect(win, (255, 255, 255), button_rect, 2, border_radius=12)

    font = pygame.font.SysFont(None, 36)
    text_surf = font.render(text, True, (255, 255, 255))
    text_rect = text_surf.get_rect(center=button_rect.center)
    win.blit(text_surf, text_rect)

    return hovered and click


def death_screen(window):
    run = True
    clock = pygame.time.Clock()
    background, bg_image = get_background("8BitBackground.png")

    pygame.mixer.music.pause()

    gameover_sound.play()

    while run:
        clock.tick(FPS)
        mouse_pos = pygame.mouse.get_pos()
        click = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                click = True

        # Draw the background
        for tile in background:
            window.blit(bg_image, tile)

        font = pygame.font.SysFont(None, 80)
        text_surf = font.render("You Died!", True, (220, 50, 50))
        text_rect = text_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 100))
        window.blit(text_surf, text_rect)

        if draw_button(window, "Restart", HEIGHT // 2 + 20, mouse_pos, click):
            run = False
            pygame.mixer.music.unpause()

        pygame.display.update()

def draw_hearts(window, health):
    for i in range(health):
        pygame.draw.ellipse(window, (255, 0, 0), pygame.Rect(10 + i*40, 10, 30, 30))

def start_menu(window):
    run = True
    clock = pygame.time.Clock()
    background, bg_image = get_background("8BitBackground.png")

    while run:
        clock.tick(FPS)
        mouse_pos = pygame.mouse.get_pos()
        click = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                click = True

        # Draw the background
        for tile in background:
            window.blit(bg_image, tile)

        font = pygame.font.SysFont(None, 80)

        if draw_button(window, "Play", HEIGHT // 2 + 20, mouse_pos, click):
            run = False
            pygame.mixer.music.unpause()

        if draw_button(window, "Close Game", HEIGHT // 2 + 100, mouse_pos, click):
            run = False
            pygame.mixer.music.unpause()

        pygame.display.update()

def main(window, initial_startup=True):
    if initial_startup == True:
        start_menu(window)
    clock = pygame.time.Clock()
    background, bg_image = get_background("8BitBackground.png")

    block_size = 96

    player = Player(100, 100, 42, 42)

    # Move apple further to the right (end of longer level)
    apple = Apple(block_size * 40, HEIGHT - block_size * 6, 32, 32)

    # Add more fire traps along the way
    fires = [
        Fire(block_size * 5, HEIGHT - block_size - 64, 16, 32),
        Fire(block_size * 25, HEIGHT - block_size - 64, 16, 32),
        Fire(block_size * 26, HEIGHT - block_size - 64, 16, 32),
        Fire(block_size * 27, HEIGHT - block_size - 64, 16, 32),
        Fire(block_size * 28, HEIGHT - block_size - 64, 16, 32),
        Fire(block_size * 29, HEIGHT - block_size - 64, 16, 32),
        Fire(block_size * 20, HEIGHT - block_size - 64, 16, 32),
        Fire(block_size * 21, HEIGHT - block_size - 64, 16, 32),
        Fire(block_size * 12 + 20, HEIGHT - block_size * 5 - 32, 16, 32),
        Fire(block_size * 16 + 10, HEIGHT - block_size * 7 - 32, 16, 32),
        Fire(block_size * 18 + 30, HEIGHT - block_size * 5 - 32, 16, 32),
        Fire(block_size * 36, HEIGHT - block_size - 64, 16, 32),
    ]

    for fire in fires:
        fire.on()

    # Extend the floor to cover a longer level
    floor = [Block(i * block_size, HEIGHT - block_size, block_size, blocktype=96)
            for i in range(-WIDTH // block_size, (WIDTH * 4) // block_size)]

    # Add more platforms to match the longer level
    blocks = [
        # Original platforms
        Block(block_size * 2, HEIGHT - block_size * 3, block_size, blocktype=0),
        Block(block_size * 3, HEIGHT - block_size * 4, block_size, blocktype=0),
        Block(block_size * 4, HEIGHT - block_size * 5, block_size, blocktype=0),
        Block(block_size * 5, HEIGHT - block_size, block_size, blocktype=0),
        Block(block_size * 7, HEIGHT - block_size * 3, block_size, blocktype=0),
        Block(block_size * 8, HEIGHT - block_size * 4, block_size, blocktype=0),
        Block(block_size * 9, HEIGHT - block_size * 5, block_size, blocktype=0),
        Block(block_size * 10, HEIGHT - block_size * 2, block_size, blocktype=0),
        Block(block_size * 10, HEIGHT - block_size * 3, block_size, blocktype=0),
        Block(block_size * 10, HEIGHT - block_size * 4, block_size, blocktype=0),
        Block(block_size * 12, HEIGHT - block_size * 5, block_size, blocktype=0),
        Block(block_size * 14, HEIGHT - block_size * 6, block_size, blocktype=0),
        Block(block_size * 16, HEIGHT - block_size * 7, block_size, blocktype=0),
        Block(block_size * 18, HEIGHT - block_size * 5, block_size, blocktype=0),
        Block(block_size * 19, HEIGHT - block_size * 5, block_size, blocktype=0),

        # New platforms
        Block(block_size * 21, HEIGHT - block_size * 3, block_size, blocktype=0),
        Block(block_size * 22, HEIGHT - block_size * 4, block_size, blocktype=0),
        Block(block_size * 23, HEIGHT - block_size * 5, block_size, blocktype=0),
        Block(block_size * 25, HEIGHT - block_size * 3, block_size, blocktype=0),
        Block(block_size * 26, HEIGHT - block_size * 4, block_size, blocktype=0),
        Block(block_size * 28, HEIGHT - block_size * 5, block_size, blocktype=0),
        Block(block_size * 30, HEIGHT - block_size * 3, block_size, blocktype=0),
        Block(block_size * 32, HEIGHT - block_size * 4, block_size, blocktype=0),
        Block(block_size * 34, HEIGHT - block_size * 5, block_size, blocktype=0),
        Block(block_size * 36, HEIGHT - block_size * 3, block_size, blocktype=0),
        Block(block_size * 38, HEIGHT - block_size * 4, block_size, blocktype=0),
    ]

    # Combine all objects
    objects = [*floor, *blocks, *fires]

    objects.append(apple)

    offset_x = 0
    scroll_area_width = 200

    run = True
    attack_cooldown = 500  # milliseconds
    last_attack_time = 0
    while run:
        current_time = pygame.time.get_ticks()

        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and player.jump_count < 2:
                    player.jump()
                    jump_sound.play()

            mouse_buttons = pygame.mouse.get_pressed()
            
            
            if mouse_buttons[2]:  # Right mouse button is index 2
                player.attack()
                if not attack_sound.get_num_channels():  # Only play if not already playing
                    attack_sound.play()
            else:
                player.attacking = False
        
         # ✅ This is OUTSIDE the event loop — checks every frame
        mouse_buttons = pygame.mouse.get_pressed()
        if mouse_buttons[2]:  # Right mouse button held
            if current_time - last_attack_time > attack_cooldown:
                player.attack()
                attack_sound.play()
                last_attack_time = current_time

        player.loop(FPS)
        for fire in fires:
            fire.loop()
        handle_move(player, objects, offset_x)
        apple.loop()

        if player.won== True:
            win_screen(window)
            main(window, initial_startup = False)  # Restart game
            return
        
         # Lose condition: player fell off the map
        if player.rect.top > HEIGHT:
            death_screen(window)
            main(window, initial_startup = False)  # Restart game
            return
        
        if player.health <= 0:
            death_screen(window)
            main(window, initial_startup = False)  # Restart game
            return  # exit current game loop after death screen
        
        draw(window, background, bg_image, player, objects, offset_x)

        if ((player.rect.right - offset_x >= WIDTH - scroll_area_width) and player.x_vel > 0) or (
                (player.rect.left - offset_x <= scroll_area_width) and player.x_vel < 0):
            offset_x += player.x_vel

    pygame.quit()
    quit()


if __name__ == "__main__":
    main(window)
