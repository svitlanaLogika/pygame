import socket
from threading import Thread
import time
from random import randint

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Дозволяємо перевикористання адреси
sock.bind(('0.0.0.0', 8081))
sock.listen(5)
sock.setblocking(False)

players = {}
conn_ids = {}
id_counter = 0

# Ініціалізація їжі
food_items = []
for _ in range(100):  # Створюємо 100 елементів їжі
    food_items.append({
        'x': randint(-2000, 2000),
        'y': randint(-2000, 2000),
        'r': 10,
        'color': (randint(0, 255), randint(0, 255), randint(0, 255))
    })


def is_connection_alive(conn):
    """Перевіряє чи з'єднання ще активне"""
    try:
        # Відправляємо невеликий пакет для перевірки з'єднання
        conn.send(b'')
        return True
    except:
        return False


def safe_send(conn, data):
    """Безпечна відправка даних"""
    try:
        if is_connection_alive(conn):
            conn.send(data)
            return True
        else:
            return False
    except Exception as e:
        print(f"Error sending data: {e}")
        return False


def handle_data():
    global id_counter, food_items
    while True:
        time.sleep(0.01)
        player_data = {}
        to_remove = []

        # Збираємо дані від всіх клієнтів
        for conn in list(players.keys()):
            try:
                data = conn.recv(64).decode().strip()
                if data and ',' in data:
                    parts = data.split(',')
                    if len(parts) == 5:
                        try:
                            pid, x, y, r = map(int, parts[:4])
                            name = parts[-1]
                            players[conn] = {'id': pid, 'x': x, 'y': y, 'r': r, 'name': name}
                            player_data[conn] = players[conn]
                        except ValueError:
                            continue
            except BlockingIOError:
                continue
            except (ConnectionResetError, ConnectionAbortedError, OSError):
                to_remove.append(conn)
                continue
            except Exception as e:
                print(f"Error receiving data: {e}")
                to_remove.append(conn)
                continue

        # Перевіряємо з'їдання їжі
        eaten_food = []
        for conn, player in player_data.items():
            if conn in to_remove:
                continue
            for i, food in enumerate(food_items):
                if i in eaten_food:
                    continue
                dx = food['x'] - player['x']
                dy = food['y'] - player['y']
                distance = (dx ** 2 + dy ** 2) ** 0.5
                if distance <= food['r'] + player['r']:
                    # Гравець з'їв їжу
                    player['r'] += int(food['r'] * 0.2)
                    players[conn] = player
                    eaten_food.append(i)

        # Видаляємо з'їдену їжу та додаємо нову
        for i in sorted(eaten_food, reverse=True):
            food_items.pop(i)
            # Додаємо нову їжу
            food_items.append({
                'x': randint(-2000, 2000),
                'y': randint(-2000, 2000),
                'r': 10,
                'color': (randint(0, 255), randint(0, 255), randint(0, 255))
            })

        # Перевіряємо колізії між гравцями
        eliminated = []
        for conn1 in player_data:
            if conn1 in eliminated or conn1 in to_remove:
                continue
            p1 = player_data[conn1]
            for conn2 in player_data:
                if conn1 == conn2 or conn2 in eliminated or conn2 in to_remove:
                    continue
                p2 = player_data[conn2]
                dx, dy = p1['x'] - p2['x'], p1['y'] - p2['y']
                distance = (dx ** 2 + dy ** 2) ** 0.5
                if distance < p1['r'] + p2['r'] and p1['r'] > p2['r'] * 1.1:
                    p1['r'] += int(p2['r'] * 0.5)
                    players[conn1] = p1
                    eliminated.append(conn2)

        # Відправляємо дані всім клієнтам
        for conn in list(players.keys()):
            if conn in to_remove:
                continue

            if conn in eliminated:
                if safe_send(conn, "LOSE".encode()):
                    print(f"Player {players[conn]['id']} eliminated")
                to_remove.append(conn)
                continue

            try:
                # Підготовка даних про гравців
                all_other_players = []
                for c, p in players.items():
                    if c != conn and c not in eliminated and c not in to_remove:
                        all_other_players.append(f"{p['id']},{p['x']},{p['y']},{p['r']},{p['name']}")

                # Підготовка даних про їжу
                food_data = []
                for food in food_items:
                    food_data.append(
                        f"{food['x']},{food['y']},{food['r']},{food['color'][0]},{food['color'][1]},{food['color'][2]}")

                # Формуємо пакет
                if all_other_players:
                    players_packet = '|'.join(all_other_players)
                else:
                    players_packet = ''

                food_packet = '|'.join(food_data)
                full_packet = f"PLAYERS|{players_packet}|FOOD|{food_packet}"

                # Безпечна відправка
                if not safe_send(conn, full_packet.encode()):
                    to_remove.append(conn)

            except Exception as e:
                print(f"Error preparing data for client: {e}")
                to_remove.append(conn)

        # Видаляємо відключених гравців
        for conn in to_remove:
            if conn in players:
                print(f"Removing player {players[conn]['id']}")
                players.pop(conn, None)
                conn_ids.pop(conn, None)
                try:
                    conn.close()
                except:
                    pass


# Запускаємо обробку даних
Thread(target=handle_data, daemon=True).start()
print("SERVER running on 0.0.0.0:8081...")
print("Use ngrok to expose this server: ngrok tcp 8081")

# Основний цикл для прийому нових підключень
while True:
    try:
        conn, addr = sock.accept()
        conn.setblocking(False)
        id_counter += 1
        players[conn] = {'id': id_counter, 'x': 0, 'y': 0, 'r': 20, 'name': f'Player{id_counter}'}
        conn_ids[conn] = id_counter

        # Надсилаємо початкові дані
        initial_data = f"{id_counter},0,0,20"
        if safe_send(conn, initial_data.encode()):
            print(f"New player connected from {addr}: ID {id_counter}")
            print(f"Total players: {len(players)}")
        else:
            # Якщо не вдалося відправити початкові дані, видаляємо гравця
            players.pop(conn, None)
            conn_ids.pop(conn, None)
            id_counter -= 1
            try:
                conn.close()
            except:
                pass
    except BlockingIOError:
        continue
    except Exception as e:
        print(f"Error accepting connection: {e}")
        continue