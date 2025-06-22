# Оновлений ch3_server.py з підтримкою скінів
import socket
from socket import AF_INET, SOCK_STREAM
from threading import Thread
import time
import json
import select


class GameServer:
    def __init__(self, host='localhost', port=8080):
        self.sock = socket.socket(AF_INET, SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((host, port))
        self.sock.listen(5)
        self.sock.setblocking(False)

        self.players = {}
        self.id_counter = 0
        self.running = True
        
        # Список доступних скінів
        self.available_skins = [
            'default', 'football', 'earth', 'mars', 'sun', 'moon',
            'fire', 'water', 'toxic', 'rainbow', 'galaxy', 'lava'
        ]

    def validate_skin(self, skin_name):
        """Перевіряє чи валідний скін"""
        return skin_name in self.available_skins

    def handle_client_data(self, conn, data):
        """Обробка даних від клієнта з валідацією та підтримкою скінів"""
        try:
            if not data or len(data.strip()) == 0:
                return False

            parts = data.strip().split(',')
            if len(parts) < 5:
                return False

            pid, x, y, r = map(int, parts[:4])
            name = parts[4][:20]  # Обмеження довжини імені
            
            # Обробка скіна (новий функціонал)
            skin = 'default'
            if len(parts) >= 6:
                requested_skin = parts[5].strip()
                if self.validate_skin(requested_skin):
                    skin = requested_skin
                else:
                    print(f"Недопустимий скін: {requested_skin}, використовується default")

            # Валідація даних
            if not (-5000 <= x <= 5000) or not (-5000 <= y <= 5000):
                return False
            if not (10 <= r <= 200):
                return False

            self.players[conn] = {
                'id': pid, 'x': x, 'y': y, 'r': r, 'name': name, 'skin': skin
            }
            return True

        except (ValueError, IndexError) as e:
            print(f"Помилка парсингу даних: {e}")
            return False

    def handle_collisions(self):
        """Обробка зіткнень між гравцями"""
        eliminated = set()
        player_list = list(self.players.items())

        for i, (conn1, p1) in enumerate(player_list):
            if conn1 in eliminated:
                continue

            for j, (conn2, p2) in enumerate(player_list[i + 1:], i + 1):
                if conn2 in eliminated:
                    continue

                dx, dy = p1['x'] - p2['x'], p1['y'] - p2['y']
                distance = (dx ** 2 + dy ** 2) ** 0.5

                # Перевірка поглинання
                if distance < max(p1['r'], p2['r']) * 0.8:
                    if p1['r'] > p2['r']:
                        p1['r'] += int(p2['r'] * 0.3)
                        self.players[conn1] = p1
                        eliminated.add(conn2)
                        print(f"Гравець {p1['name']} ({p1['skin']}) поглинув гравця {p2['name']} ({p2['skin']})")
                    elif p2['r'] > p1['r']:
                        p2['r'] += int(p1['r'] * 0.3)
                        self.players[conn2] = p2
                        eliminated.add(conn1)
                        print(f"Гравець {p2['name']} ({p2['skin']}) поглинув гравця {p1['name']} ({p1['skin']})")

        return eliminated

    def broadcast_game_state(self, eliminated):
        """Розсилка стану гри всім клієнтам з інформацією про скіни"""
        to_remove = []

        for conn in list(self.players.keys()):
            if conn in eliminated:
                try:
                    conn.send("LOSE".encode())
                except:
                    pass
                to_remove.append(conn)
                continue

            try:
                # Формування пакету з даними інших гравців включаючи скіни
                other_players = [
                    f"{p['id']},{p['x']},{p['y']},{p['r']},{p['name']},{p['skin']}"
                    for c, p in self.players.items()
                    if c != conn and c not in eliminated
                ]
                packet = '|'.join(other_players) + '|'
                conn.send(packet.encode())

            except (ConnectionResetError, BrokenPipeError):
                to_remove.append(conn)
            except Exception as e:
                print(f"Помилка при відправці даних: {e}")
                to_remove.append(conn)

        # Видалення відключених клієнтів
        for conn in to_remove:
            player_info = self.players.get(conn, {})
            if player_info:
                print(f"Гравець {player_info.get('name', 'Unknown')} відключився")
            self.players.pop(conn, None)
            try:
                conn.close()
            except:
                pass

    def game_loop(self):
        """Основний ігровий цикл"""
        while self.running:
            time.sleep(1 / 60)  # 60 FPS

            # Збір даних від клієнтів
            to_remove = []
            for conn in list(self.players.keys()):
                try:
                    ready, _, _ = select.select([conn], [], [], 0)
                    if ready:
                        data = conn.recv(1024).decode().strip()
                        if not self.handle_client_data(conn, data):
                            to_remove.append(conn)
                except:
                    to_remove.append(conn)

            # Видалення проблемних з'єднань
            for conn in to_remove:
                self.players.pop(conn, None)

            # Обробка зіткнень
            eliminated = self.handle_collisions()

            # Розсилка оновлень
            self.broadcast_game_state(eliminated)

    def accept_connections(self):
        """Прийом нових підключень"""
        while self.running:
            try:
                ready, _, _ = select.select([self.sock], [], [], 0.1)
                if ready:
                    conn, addr = self.sock.accept()
                    conn.setblocking(False)

                    self.id_counter += 1
                    self.players[conn] = {
                        'id': self.id_counter, 'x': 0, 'y': 0, 'r': 20, 
                        'name': None, 'skin': 'default'
                    }

                    # Відправка початкових даних (тепер з підтримкою скінів)
                    init_data = f"{self.id_counter},0,0,20"
                    conn.send(init_data.encode())
                    print(f"Новий гравець підключився: {addr} (ID: {self.id_counter})")

            except:
                continue

    def get_server_stats(self):
        """Повертає статистику сервера"""
        skin_stats = {}
        for player in self.players.values():
            skin = player.get('skin', 'default')
            skin_stats[skin] = skin_stats.get(skin, 0) + 1
        
        return {
            'total_players': len(self.players),
            'skin_distribution': skin_stats,
            'available_skins': self.available_skins
        }

    def start(self):
        """Запуск сервера"""
        print("Сервер Agario запущено на localhost:8080")
        print(f"Доступні скіни: {', '.join(self.available_skins)}")

        # Запуск потоків
        game_thread = Thread(target=self.game_loop, daemon=True)
        accept_thread = Thread(target=self.accept_connections, daemon=True)

        game_thread.start()
        accept_thread.start()

        try:
            last_stats_time = time.time()
            while self.running:
                time.sleep(1)
                
                # Виводимо статистику кожні 30 секунд
                if time.time() - last_stats_time > 30:
                    stats = self.get_server_stats()
                    print(f"Статистика сервера: {stats['total_players']} гравців")
                    if stats['skin_distribution']:
                        print(f"Розподіл скінів: {stats['skin_distribution']}")
                    last_stats_time = time.time()
                    
        except KeyboardInterrupt:
            print("Завершення роботи сервера...")
            self.running = False
            print("Сервер зупинено")


if __name__ == "__main__":
    server = GameServer()
    server.start()