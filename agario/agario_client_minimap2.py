from math import hypot
from socket import socket, AF_INET, SOCK_STREAM
from pygame import *
from threading import Thread
from random import randint
from menu import ConnectWindow

win = ConnectWindow()
win.mainloop()

name = win.name
port = win.port
host = win.host
sock = socket(AF_INET, SOCK_STREAM)
sock.connect((host, port))
my_data = list(map(int, sock.recv(64).decode().strip().split(',')))
my_id = my_data[0]
my_player = my_data[1:]
sock.setblocking(False)

init()
window = display.set_mode((1000, 1000))
clock = time.Clock()
f = font.Font(None, 50)
all_players = []
running = True
lose = False

# === ДОДАНО: Налаштування міні-карти ===
MINIMAP_SIZE = 150  # Розмір міні-карти в пікселях
MINIMAP_POS = (1000 - MINIMAP_SIZE - 10, 10)  # Позиція міні-карти (правий верхній кут)
WORLD_SIZE = 4000  # Розмір ігрового світу (-2000 до 2000 по кожній осі)
minimap_surface = Surface((MINIMAP_SIZE, MINIMAP_SIZE))  # Поверхня для малювання міні-карти
show_minimap = True  # Флаг для показу/приховування міні-карти (за замовчуванням увімкнена)


def receive_data():
    global all_players, running, lose
    while running:
        try:
            data = sock.recv(4096).decode().strip()
            if data == "LOSE":
                lose = True
            elif data:
                parts = data.strip('|').split('|')

                all_players = [list(map(int, p.split(',')[:4])) + [p.split(',')[4]] for p in parts if
                               len(p.split(',')) == 5]

                print(all_players)
        except:
            pass


Thread(target=receive_data, daemon=True).start()


class Eat:
    def __init__(self, x, y, r, c):
        self.x = x
        self.y = y
        self.radius = r
        self.color = c

    def check_collision(self, player_x, player_y, player_r):
        dx = self.x - player_x
        dy = self.y - player_y
        return hypot(dx, dy) <= self.radius + player_r


# === ДОДАНО: Функція для малювання міні-карти ===
def draw_minimap():
    """Малює міні-карту з позиціями всіх гравців"""
    # Очищуємо поверхню міні-карти темно-сірим кольором
    minimap_surface.fill((50, 50, 50))

    # Малюємо рамку міні-карти
    draw.rect(minimap_surface, (100, 100, 100), (0, 0, MINIMAP_SIZE, MINIMAP_SIZE), 2)

    # Функція для конвертації світових координат в координати міні-карти
    def world_to_minimap(world_x, world_y):
        # Конвертуємо координати з діапазону [-2000, 2000] в [0, MINIMAP_SIZE]
        minimap_x = int((world_x + WORLD_SIZE / 2) * MINIMAP_SIZE / WORLD_SIZE)
        minimap_y = int((world_y + WORLD_SIZE / 2) * MINIMAP_SIZE / WORLD_SIZE)
        # Обмежуємо координати межами міні-карти
        minimap_x = max(0, min(MINIMAP_SIZE - 1, minimap_x))
        minimap_y = max(0, min(MINIMAP_SIZE - 1, minimap_y))
        return minimap_x, minimap_y

    # Малюємо інших гравців на міні-карті (червоні точки)
    for player in all_players:
        if player[0] != my_id:  # Не малюємо себе тут
            mx, my = world_to_minimap(player[1], player[2])
            # Розмір точки залежить від розміру гравця (мінімум 2, максимум 8 пікселів)
            point_size = max(2, min(8, player[3] // 10))
            draw.circle(minimap_surface, (255, 100, 100), (mx, my), point_size)

    # Малюємо свого гравця (зелена точка) в останню чергу, щоб він був зверху
    my_mx, my_my = world_to_minimap(my_player[0], my_player[1])
    my_point_size = max(3, min(10, my_player[2] // 8))
    draw.circle(minimap_surface, (100, 255, 100), (my_mx, my_my), my_point_size)

    # Малюємо центральну точку світу (біла точка)
    center_x, center_y = world_to_minimap(0, 0)
    draw.circle(minimap_surface, (255, 255, 255), (center_x, center_y), 1)

    # Відображаємо міні-карту на головному екрані
    window.blit(minimap_surface, MINIMAP_POS)

    # Додаємо напівпрозору рамку навколо міні-карти на головному екрані
    draw.rect(window, (255, 255, 255),
              (MINIMAP_POS[0] - 2, MINIMAP_POS[1] - 2, MINIMAP_SIZE + 4, MINIMAP_SIZE + 4), 2)


eats = [Eat(randint(-2000, 2000), randint(-2000, 2000), 10,
            (randint(0, 255), randint(0, 255), randint(0, 255)))
        for _ in range(300)]
name_font = font.Font(None, 20)

while running:
    for e in event.get():
        if e.type == QUIT:
            running = False
        # === ДОДАНО: Обробка клавіші M для показу/приховування міні-карти ===
        elif e.type == KEYDOWN:
            if e.key == K_m:  # Натискання клавіші M
                show_minimap = not show_minimap  # Переключаємо стан показу міні-карти
                print(f"Міні-карта: {'Увімкнена' if show_minimap else 'Вимкнена'}")  # Повідомлення в консоль

    window.fill((255, 255, 255))
    scale = max(0.3, min(50 / my_player[2], 1.5))

    # Малюємо інших гравців
    for p in all_players:
        if p[0] == my_id: continue
        sx = int((p[1] - my_player[0]) * scale + 500)
        sy = int((p[2] - my_player[1]) * scale + 500)
        draw.circle(window, (255, 0, 0), (sx, sy), int(p[3] * scale))
        name_text = name_font.render(f'{p[4]}', 1, (0, 0, 0))
        window.blit(name_text, (sx, sy))

    # Малюємо свого гравця
    draw.circle(window, (0, 255, 0), (500, 500), int(my_player[2] * scale))

    # Малюємо їжу
    to_remove = []
    for eat in eats:
        if eat.check_collision(my_player[0], my_player[1], my_player[2]):
            to_remove.append(eat)
            my_player[2] += int(eat.radius * 0.2)
        else:
            sx = int((eat.x - my_player[0]) * scale + 500)
            sy = int((eat.y - my_player[1]) * scale + 500)
            draw.circle(window, eat.color, (sx, sy), int(eat.radius * scale))

    for eat in to_remove:
        eats.remove(eat)

    # === ДОДАНО: Виклик функції малювання міні-карти ===
    # Малюємо міні-карту після всіх інших елементів, щоб вона була зверху
    # Але тільки якщо увімкнений показ міні-карти
    if show_minimap:
        draw_minimap()

    # Показуємо повідомлення про програш
    if lose:
        t = f.render('U lose!', 1, (244, 0, 0))
        window.blit(t, (400, 500))

    # === ДОДАНО: Показуємо підказку щодо управління міні-картою ===
    # Малюємо підказку в лівому нижньому куті екрану
    hint_font = font.Font(None, 24)
    hint_text = hint_font.render(f'M - {"Hide" if show_minimap else "Show"} minimap', 1, (100, 100, 100))
    window.blit(hint_text, (10, 970))

    display.update()
    clock.tick(60)

    # Обробка руху гравця
    if not lose:
        keys = key.get_pressed()
        if keys[K_w]: my_player[1] -= 15
        if keys[K_s]: my_player[1] += 15
        if keys[K_a]: my_player[0] -= 15
        if keys[K_d]: my_player[0] += 15

        try:
            msg = f"{my_id},{my_player[0]},{my_player[1]},{my_player[2]},{name}"
            sock.send(msg.encode())
        except:
            pass

quit()
