from math import hypot
import socket
import pygame
from pygame import display, font, event, key, draw, QUIT, K_w, K_s, K_a, K_d
from threading import Thread
from random import randint
from menu import ConnectWindow
import time

win = ConnectWindow()
win.mainloop()

name = win.name
port = win.port
host = win.host

# Створюємо сокет з додатковими налаштуваннями
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)  # Включаємо keep-alive

try:
    sock.connect((host, port))
    print(f"Connected to {host}:{port}")
except Exception as e:
    print(f"Connection failed: {e}")
    exit()

# Обробка початкових даних
try:
    initial_data = sock.recv(64).decode().strip()
    print(f"Received initial data: {initial_data}")
    if initial_data and ',' in initial_data:
        my_data = list(map(int, initial_data.split(',')))
        my_id = my_data[0]
        my_player = my_data[1:]
    else:
        raise ValueError("Invalid initial data format")
except Exception as e:
    print(f"Error parsing initial data: {e}")
    # Встановлюємо значення за замовчуванням
    my_id = 1
    my_player = [0, 0, 20]

sock.setblocking(False)

pygame.init()
window = display.set_mode((1000, 1000))
clock = pygame.time.Clock()
f = font.Font(None, 50)
all_players = []
eats = []
running = True
lose = False
connection_lost = False


def is_connection_alive():
    """Перевіряє чи з'єднання ще активне"""
    global connection_lost
    try:
        # Спробуємо отримати дані без блокування
        sock.recv(0)
        return True
    except BlockingIOError:
        return True  # Нормально для неблокуючих сокетів
    except (ConnectionResetError, ConnectionAbortedError, OSError):
        connection_lost = True
        return False
    except Exception:
        return True


def safe_send(data):
    """Безпечна відправка даних"""
    global connection_lost
    try:
        if not connection_lost:
            sock.send(data)
            return True
        return False
    except (ConnectionResetError, ConnectionAbortedError, OSError):
        connection_lost = True
        print("Connection lost while sending data")
        return False
    except Exception as e:
        print(f"Error sending data: {e}")
        return False


def receive_data():
    global all_players, running, lose, eats, connection_lost
    consecutive_errors = 0

    while running and not connection_lost:
        try:
            if not is_connection_alive():
                break

            data = sock.recv(8192).decode().strip()

            if not data:
                consecutive_errors += 1
                if consecutive_errors > 100:  # Якщо багато порожніх пакетів підряд
                    print("Too many empty packets, connection may be lost")
                    break
                time.sleep(0.01)
                continue

            consecutive_errors = 0  # Скидаємо лічильник при успішному отриманні даних

            if data == "LOSE":
                lose = True
                print("You lost!")
            elif data.startswith("PLAYERS|") or data.startswith("FOOD|"):
                # Обробляємо дані гри
                try:
                    parts = data.split('|')

                    # Перевіряємо наявність необхідних маркерів
                    if 'PLAYERS' not in parts or 'FOOD' not in parts:
                        print(f"Invalid data format: {data[:100]}...")
                        continue

                    players_start = parts.index('PLAYERS') + 1
                    food_start = parts.index('FOOD') + 1

                    # Обробка даних гравців
                    new_players = []
                    for i in range(players_start, len(parts)):
                        if i < len(parts) and parts[i] == 'FOOD':
                            break
                        if i < len(parts) and parts[i] and ',' in parts[i]:
                            player_parts = parts[i].split(',')
                            if len(player_parts) == 5:
                                try:
                                    player_data = list(map(int, player_parts[:4])) + [player_parts[4]]
                                    new_players.append(player_data)
                                except ValueError:
                                    continue
                    all_players = new_players

                    # Обробка даних їжі
                    new_eats = []
                    for i in range(food_start, len(parts)):
                        if i < len(parts) and parts[i] and ',' in parts[i]:
                            food_parts = parts[i].split(',')
                            if len(food_parts) == 6:
                                try:
                                    x, y, r, color_r, color_g, color_b = map(int, food_parts)
                                    new_eats.append(Eat(x, y, r, (color_r, color_g, color_b)))
                                except ValueError:
                                    continue
                    eats = new_eats

                    # print(f"Received {len(all_players)} players, {len(eats)} food items")
                except Exception as e:
                    print(f"Error parsing game data: {e}")
                    print(f"Data received: {data[:200]}...")
                    continue
            else:
                # Невідомий формат даних
                print(f"Unknown data format: {data[:50]}...")

        except BlockingIOError:
            pass
        except (ConnectionResetError, ConnectionAbortedError, OSError):
            print("Connection lost to server")
            connection_lost = True
            break
        except Exception as e:
            print(f"Unexpected error in receive_data: {e}")
            consecutive_errors += 1
            if consecutive_errors > 50:
                print("Too many consecutive errors, stopping")
                break

        time.sleep(0.01)

    running = False
    print("Receive thread stopped")


# Запускаємо потік для отримання даних
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


name_font = font.Font(None, 20)
last_send_time = 0
send_interval = 1 / 60  # 60 FPS для відправки даних

while running and not connection_lost:
    current_time = time.time()

    for e in event.get():
        if e.type == QUIT:
            running = False

    # Обробка введення
    if not lose:
        keys = key.get_pressed()
        moved = False
        if keys[K_w]:
            my_player[1] -= 15
            moved = True
        if keys[K_s]:
            my_player[1] += 15
            moved = True
        if keys[K_a]:
            my_player[0] -= 15
            moved = True
        if keys[K_d]:
            my_player[0] += 15
            moved = True

        # Відправляємо дані лише якщо гравець рухається або минув певний інтервал
        if moved or current_time - last_send_time >= send_interval:
            msg = f"{my_id},{my_player[0]},{my_player[1]},{my_player[2]},{name}"
            if safe_send(msg.encode()):
                last_send_time = current_time
            else:
                print("Failed to send player data")
                running = False

    # Рендеринг
    window.fill((255, 255, 255))
    scale = max(0.3, min(50 / my_player[2], 1.5))

    # Малюємо інших гравців
    for p in all_players:
        if p[0] == my_id:
            continue
        sx = int((p[1] - my_player[0]) * scale + 500)
        sy = int((p[2] - my_player[1]) * scale + 500)
        draw.circle(window, (255, 0, 0), (sx, sy), int(p[3] * scale))
        name_text = name_font.render(f'{p[4]}', 1, (0, 0, 0))
        window.blit(name_text, (sx - name_text.get_width() // 2, sy - name_text.get_height() // 2))

    # Малюємо свого гравця
    draw.circle(window, (0, 255, 0), (500, 500), int(my_player[2] * scale))
    my_name_text = name_font.render(name, 1, (0, 0, 0))
    window.blit(my_name_text, (500 - my_name_text.get_width() // 2, 500 - my_name_text.get_height() // 2))

    # Малюємо їжу та перевіряємо колізії
    to_remove = []
    for eat in eats:
        if eat.check_collision(my_player[0], my_player[1], my_player[2]):
            to_remove.append(eat)
            my_player[2] += int(eat.radius * 0.2)
        else:
            sx = int((eat.x - my_player[0]) * scale + 500)
            sy = int((eat.y - my_player[1]) * scale + 500)
            if 0 <= sx <= 1000 and 0 <= sy <= 1000:  # Малюємо лише видиму їжу
                draw.circle(window, eat.color, (sx, sy), max(1, int(eat.radius * scale)))

    # Видаляємо з'їдену їжу
    for eat in to_remove:
        if eat in eats:
            eats.remove(eat)

    # Відображаємо повідомлення про програш
    if lose:
        t = f.render('You lose!', 1, (244, 0, 0))
        window.blit(t, (400, 500))

    # Відображаємо повідомлення про втрату з'єднання
    if connection_lost:
        t = f.render('Connection Lost!', 1, (244, 0, 0))
        window.blit(t, (350, 450))

    display.update()
    clock.tick(60)

# Закриваємо з'єднання
try:
    sock.close()
except:
    pass

print("Client stopped")
pygame.quit()