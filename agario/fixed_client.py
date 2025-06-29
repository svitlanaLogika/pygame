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

# Виправлена обробка початкових даних
try:
    initial_data = sock.recv(64).decode().strip()
    print(f"Received initial data: '{initial_data}'")
    
    # Сервер надсилає: "id,x,y,r"
    parts = initial_data.split(',')
    my_id = int(parts[0])
    
    # Використовуємо дані від сервера (x=0, y=0, r=20)
    if len(parts) >= 4:
        my_player = [int(parts[1]), int(parts[2]), int(parts[3])]  # [x, y, radius]
    else:
        my_player = [0, 0, 20]  # За замовчуванням в центрі
        
    print(f"My ID: {my_id}, My position: {my_player}")

except Exception as e:
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
            if not data:
                continue
                
            if data == "LOSE":
                lose = True
                print("You lost!")
            else:
                # Обробка даних інших гравців
                if data.endswith('|'):
                    data = data[:-1]  # Видаляємо останній |
                
                if data:  # Якщо є дані
                    parts = data.split('|')
                    all_players = []
                    
                    for part in parts:
                        if part.strip():  # Якщо частина не пуста
                            player_data = part.split(',')
                            if len(player_data) >= 5:
                                try:
                                    player_info = [
                                        int(player_data[0]),  # id
                                        int(player_data[1]),  # x
                                        int(player_data[2]),  # y
                                        int(player_data[3]),  # radius
                                        player_data[4]        # name
                                    ]
                                    all_players.append(player_info)
                                except ValueError:
                                    continue
                    
                    print(f"Players received: {len(all_players)}")
                else:
                    all_players = []  # Немає інших гравців
                    
        except Exception as e:
            print(f"Error receiving data: {e}")
            continue


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

while running:
    for e in event.get():
        if e.type == QUIT:
            running = False

    window.fill((255, 255, 255))
    scale = max(0.3, min(50 / my_player[2], 1.5))

    # Відображення інших гравців
    print(f"Drawing {len(all_players)} other players")
    for p in all_players:
        if p[0] == my_id:  # Пропускаємо себе
            continue
            
        # Обчислення позиції на екрані
        sx = int((p[1] - my_player[0]) * scale + 500)
        sy = int((p[2] - my_player[1]) * scale + 500)
        
        # Малюємо гравця тільки якщо він на екрані
        if -100 <= sx <= 1100 and -100 <= sy <= 1100:
            draw.circle(window, (255, 0, 0), (sx, sy), max(1, int(p[3] * scale)))
            
            # Відображення імені
            if len(p) > 4 and p[4]:
                name_text = name_font.render(str(p[4]), True, (0, 0, 0))
                text_rect = name_text.get_rect(center=(sx, sy - int(p[3] * scale) - 15))
                window.blit(name_text, text_rect)

    # Відображення свого гравця (завжди в центрі екрану)
    draw.circle(window, (0, 255, 0), (500, 500), int(my_player[2] * scale))
    
    # Відображення свого імені
    if name:
        my_name_text = name_font.render(str(name), True, (0, 0, 0))
        text_rect = my_name_text.get_rect(center=(500, 500 - int(my_player[2] * scale) - 15))
        window.blit(my_name_text, text_rect)

    # Відображення їжі
    to_remove = []
    for eat in eats:
        if eat.check_collision(my_player[0], my_player[1], my_player[2]):
            to_remove.append(eat)
            my_player[2] += int(eat.radius * 0.2)
        else:
            sx = int((eat.x - my_player[0]) * scale + 500)
            sy = int((eat.y - my_player[1]) * scale + 500)
            if -50 <= sx <= 1050 and -50 <= sy <= 1050:
                draw.circle(window, eat.color, (sx, sy), max(1, int(eat.radius * scale)))

    for eat in to_remove:
        eats.remove(eat)

    if lose:
        t = f.render('You lose!', True, (255, 0, 0))
        window.blit(t, (400, 500))

    # Відображення інформації
    info_text = f"My ID: {my_id}, Players: {len(all_players)}, Pos: ({my_player[0]}, {my_player[1]})"
    debug_surface = font.Font(None, 24).render(info_text, True, (0, 0, 0))
    window.blit(debug_surface, (10, 10))

    display.update()
    clock.tick(60)

    # Управління (тільки якщо не програв)
    if not lose:
        keys = key.get_pressed()
        speed = max(5, 20 - my_player[2] // 10)  # Швидкість залежить від розміру
        
        if keys[K_w]: my_player[1] -= speed
        if keys[K_s]: my_player[1] += speed
        if keys[K_a]: my_player[0] -= speed
        if keys[K_d]: my_player[0] += speed

        # Відправка даних на сервер
        try:
            msg = f"{my_id},{my_player[0]},{my_player[1]},{my_player[2]},{name}"
            sock.send(msg.encode())
        except Exception as e:
            print(f"Error sending data: {e}")

quit()