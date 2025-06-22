from math import hypot, sin, cos, pi
from socket import socket, AF_INET, SOCK_STREAM
from pygame import *
from threading import Thread
from random import randint
from menu import ConnectWindow

# Система скінів
class SkinManager:
    def __init__(self):
        self.skins = {
            'default': {'type': 'color', 'color': (0, 255, 0)},
            'football': {'type': 'pattern', 'base_color': (255, 255, 255), 'pattern_color': (0, 0, 0)},
            'earth': {'type': 'gradient', 'colors': [(0, 100, 200), (0, 150, 50), (139, 69, 19)]},
            'mars': {'type': 'gradient', 'colors': [(200, 50, 50), (150, 30, 30), (100, 20, 20)]},
            'sun': {'type': 'gradient', 'colors': [(255, 255, 0), (255, 200, 0), (255, 150, 0)]},
            'moon': {'type': 'gradient', 'colors': [(200, 200, 200), (150, 150, 150), (100, 100, 100)]},
            'fire': {'type': 'animated', 'colors': [(255, 0, 0), (255, 100, 0), (255, 200, 0)]},
            'water': {'type': 'animated', 'colors': [(0, 150, 255), (0, 200, 255), (100, 220, 255)]},
            'toxic': {'type': 'animated', 'colors': [(50, 255, 50), (100, 255, 100), (150, 255, 150)]},
            'rainbow': {'type': 'rainbow'},
            'galaxy': {'type': 'stars', 'base_color': (20, 20, 50)},
            'lava': {'type': 'lava', 'colors': [(255, 50, 0), (200, 0, 0), (100, 0, 0)]}
        }
        self.current_skin = 'default'
        self.animation_time = 0
        
    def get_skin_color(self, skin_name, time_offset=0):
        """Повертає колір для скіна з урахуванням анімації"""
        if skin_name not in self.skins:
            skin_name = 'default'
            
        skin = self.skins[skin_name]
        
        if skin['type'] == 'color':
            return skin['color']
        elif skin['type'] == 'gradient':
            # Статичний градієнт
            return skin['colors'][0]
        elif skin['type'] == 'animated':
            # Анімований колір
            colors = skin['colors']
            index = int((self.animation_time + time_offset) * 5) % len(colors)
            return colors[index]
        elif skin['type'] == 'rainbow':
            # Райдужний ефект
            hue = (self.animation_time * 100 + time_offset) % 360
            return self.hsv_to_rgb(hue, 100, 100)
        else:
            return (0, 255, 0)
    
    def hsv_to_rgb(self, h, s, v):
        """Конвертація HSV в RGB"""
        h = h / 60.0
        s = s / 100.0
        v = v / 100.0
        
        c = v * s
        x = c * (1 - abs((h % 2) - 1))
        m = v - c
        
        if 0 <= h < 1:
            r, g, b = c, x, 0
        elif 1 <= h < 2:
            r, g, b = x, c, 0
        elif 2 <= h < 3:
            r, g, b = 0, c, x
        elif 3 <= h < 4:
            r, g, b = 0, x, c
        elif 4 <= h < 5:
            r, g, b = x, 0, c
        else:
            r, g, b = c, 0, x
            
        return (int((r + m) * 255), int((g + m) * 255), int((b + m) * 255))
    
    def draw_skin(self, surface, skin_name, pos, radius, player_id=0):
        """Малює скін на поверхні"""
        if skin_name not in self.skins:
            skin_name = 'default'
            
        skin = self.skins[skin_name]
        x, y = pos
        
        if skin['type'] == 'color':
            draw.circle(surface, skin['color'], (x, y), radius)
            
        elif skin['type'] == 'pattern' and skin_name == 'football':
            # Футбольний м'яч
            draw.circle(surface, skin['base_color'], (x, y), radius)
            # Малюємо чорні лінії футбольного м'яча
            for i in range(6):
                angle = i * pi / 3
                start_x = x + int(cos(angle) * radius * 0.7)
                start_y = y + int(sin(angle) * radius * 0.7)
                end_x = x + int(cos(angle + pi/3) * radius * 0.7)
                end_y = y + int(sin(angle + pi/3) * radius * 0.7)
                draw.line(surface, skin['pattern_color'], (start_x, start_y), (end_x, end_y), max(1, radius//10))
                
        elif skin['type'] == 'gradient':
            # Градієнтний ефект
            colors = skin['colors']
            layers = len(colors)
            for i, color in enumerate(colors):
                layer_radius = radius * (layers - i) // layers
                if layer_radius > 0:
                    draw.circle(surface, color, (x, y), layer_radius)
                    
        elif skin['type'] == 'animated':
            # Анімований скін
            color = self.get_skin_color(skin_name, player_id * 10)
            draw.circle(surface, color, (x, y), radius)
            # Додаємо пульсуючий ефект
            pulse_radius = radius + int(sin(self.animation_time * 10 + player_id) * radius * 0.1)
            draw.circle(surface, color, (x, y), max(radius//2, pulse_radius), max(1, radius//15))
            
        elif skin['type'] == 'rainbow':
            # Райдужний скін
            color = self.get_skin_color(skin_name, player_id * 30)
            draw.circle(surface, color, (x, y), radius)
            
        elif skin['type'] == 'stars':
            # Галактичний скін зі зірками
            draw.circle(surface, skin['base_color'], (x, y), radius)
            # Додаємо зірки
            import random
            random.seed(player_id)  # Фіксований seed для стабільності зірок
            for _ in range(radius // 3):
                star_x = x + random.randint(-radius//2, radius//2)
                star_y = y + random.randint(-radius//2, radius//2)
                if hypot(star_x - x, star_y - y) <= radius:
                    draw.circle(surface, (255, 255, 255), (star_x, star_y), max(1, radius//20))
                    
        elif skin['type'] == 'lava':
            # Лавовий ефект
            colors = skin['colors']
            for i, color in enumerate(colors):
                offset = int(sin(self.animation_time * 5 + i + player_id) * radius * 0.1)
                layer_radius = radius * (len(colors) - i) // len(colors) + offset
                if layer_radius > 0:
                    draw.circle(surface, color, (x, y), abs(layer_radius))
        
        # Додаємо обводку
        draw.circle(surface, (0, 0, 0), (x, y), radius, max(1, radius//20))
    
    def update_animation(self, dt):
        """Оновлює час анімації"""
        self.animation_time += dt


win = ConnectWindow()
win.mainloop()

name = win.name
port = win.port
host = win.host
selected_skin = getattr(win, 'selected_skin', 'default')  # Отримуємо вибраний скін

sock = socket(AF_INET, SOCK_STREAM)
sock.connect((host, port))

# Ініціалізація менеджера скінів
skin_manager = SkinManager()
skin_manager.current_skin = selected_skin

# Fixed: Handle different data formats and add error handling
try:
    initial_data = sock.recv(64).decode().strip()
    print(f"Received initial data: '{initial_data}'")

    if '|' in initial_data:
        parts = initial_data.split('|')
        if ',' in parts[0]:
            my_data = list(map(int, parts[0].split(',')))
        else:
            my_data = [int(parts[0])]
    else:
        my_data = list(map(int, initial_data.split(',')))

    my_id = my_data[0]

    if len(my_data) > 1:
        my_player = my_data[1:]
    else:
        my_player = [randint(-1000, 1000), randint(-1000, 1000), 20]

except (ValueError, IndexError) as e:
    print(f"Error parsing initial data: {e}")
    my_id = 1
    my_player = [0, 0, 20]

sock.setblocking(False)

init()
window = display.set_mode((1000, 1000))
clock = time.Clock()
f = font.Font(None, 50)
all_players = []
running = True
lose = False

def receive_data():
    global all_players, running, lose
    while running:
        try:
            data = sock.recv(4096).decode().strip()
            if data == "LOSE":
                lose = True
            elif data:
                parts = data.strip('|').split('|')
                all_players = []
                for p in parts:
                    if len(p.split(',')) >= 5:
                        player_data = p.split(',')
                        # Розширюємо дані гравця для включення скіна
                        if len(player_data) == 5:
                            # Старий формат без скіна
                            player_info = list(map(int, player_data[:4])) + [player_data[4], 'default']
                        else:
                            # Новий формат зі скіном
                            player_info = list(map(int, player_data[:4])) + [player_data[4], player_data[5]]
                        all_players.append(player_info)
        except Exception as e:
            print(f"Error receiving data: {e}")
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

eats = [Eat(randint(-2000, 2000), randint(-2000, 2000), 10,
            (randint(0, 255), randint(0, 255), randint(0, 255)))
        for _ in range(300)]
name_font = font.Font(None, 20)

# Додаємо інтерфейс вибору скіна
def draw_skin_selector():
    """Малює селектор скінів"""
    skins_list = list(skin_manager.skins.keys())
    y_offset = 10
    x_offset = 10
    
    # Фон для селектора
    selector_surface = Surface((200, len(skins_list) * 25 + 20))
    selector_surface.fill((200, 200, 200))
    selector_surface.set_alpha(200)
    window.blit(selector_surface, (x_offset, y_offset))
    
    # Заголовок
    title_text = name_font.render("Скіни (1-9):", True, (0, 0, 0))
    window.blit(title_text, (x_offset + 5, y_offset + 5))
    
    # Список скінів
    for i, skin_name in enumerate(skins_list[:9]):  # Показуємо тільки перші 9
        y_pos = y_offset + 25 + i * 20
        color = (0, 150, 0) if skin_name == skin_manager.current_skin else (0, 0, 0)
        skin_text = name_font.render(f"{i+1}. {skin_name}", True, color)
        window.blit(skin_text, (x_offset + 5, y_pos))
        
        # Мініатюра скіна
        skin_manager.draw_skin(window, skin_name, (x_offset + 180, y_pos + 10), 8, 0)

# Основний ігровий цикл
dt = 0
show_skin_selector = False

while running:
    dt = clock.tick(60) / 1000.0  # Дельта час в секундах
    skin_manager.update_animation(dt)
    
    for e in event.get():
        if e.type == QUIT:
            running = False
        elif e.type == KEYDOWN:
            # Перемикання скінів клавішами 1-9
            if K_1 <= e.key <= K_9:
                skin_index = e.key - K_1
                skins_list = list(skin_manager.skins.keys())
                if skin_index < len(skins_list):
                    skin_manager.current_skin = skins_list[skin_index]
            # Показати/сховати селектор скінів
            elif e.key == K_TAB:
                show_skin_selector = not show_skin_selector

    window.fill((255, 255, 255))
    scale = max(0.3, min(50 / my_player[2], 1.5))

    # Малюємо інших гравців з їх скінами
    for p in all_players:
        if p[0] == my_id: 
            continue
        sx = int((p[1] - my_player[0]) * scale + 500)
        sy = int((p[2] - my_player[1]) * scale + 500)
        radius = int(p[3] * scale)
        
        # Отримуємо скін гравця (якщо є) або використовуємо default
        player_skin = p[5] if len(p) > 5 else 'default'
        skin_manager.draw_skin(window, player_skin, (sx, sy), radius, p[0])
        
        # Ім'я гравця
        name_text = name_font.render(f'{p[4]}', True, (0, 0, 0))
        text_rect = name_text.get_rect(center=(sx, sy + radius + 15))
        window.blit(name_text, text_rect)

    # Малюємо свого гравця з вибраним скіном
    player_radius = int(my_player[2] * scale)
    skin_manager.draw_skin(window, skin_manager.current_skin, (500, 500), player_radius, my_id)

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

    # Показуємо селектор скінів
    if show_skin_selector:
        draw_skin_selector()

    # Показуємо поточний скін
    current_skin_text = name_font.render(f"Скін: {skin_manager.current_skin}", True, (0, 0, 0))
    window.blit(current_skin_text, (10, window.get_height() - 30))

    if lose:
        t = f.render('U lose!', True, (244, 0, 0))
        text_rect = t.get_rect(center=(500, 500))
        window.blit(t, text_rect)

    display.update()

    if not lose:
        keys = key.get_pressed()
        if keys[K_w]: my_player[1] -= 15
        if keys[K_s]: my_player[1] += 15
        if keys[K_a]: my_player[0] -= 15
        if keys[K_d]: my_player[0] += 15

        try:
            # Відправляємо дані з інформацією про скін
            msg = f"{my_id},{my_player[0]},{my_player[1]},{my_player[2]},{name},{skin_manager.current_skin}"
            sock.send(msg.encode())
        except Exception as e:
            print(f"Error sending data: {e}")
            pass

quit()