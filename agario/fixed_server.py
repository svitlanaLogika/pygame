import socket
from socket import AF_INET, SOCK_STREAM
from threading import Thread
import time
import select


class GameServer:
    def __init__(self, host='0.0.0.0', port=8080):  # Змінено на 0.0.0.0 для ngrok
        self.sock = socket.socket(AF_INET, SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((host, port))
        self.sock.listen(10)  # Збільшено кількість підключень
        self.sock.setblocking(False)

        self.players = {}
        self.id_counter = 0
        self.running = True
        print(f"Сервер запущено на {host}:{port}")

    def handle_client_data(self, conn, data):
        """Обробка даних від клієнта з валідацією"""
        try:
            if not data or len(data.strip()) == 0:
                return False

            parts = data.strip().split(',')
            if len(parts) != 5:
                print(f"Неправильний формат даних: {parts}")
                return False

            pid, x, y, r = map(int, parts[:4])
            name = parts[4][:20] if parts[4] else f"Player{pid}"

            # Валідація координат і розміру
            x = max(-5000, min(5000, x))
            y = max(-5000, min(5000, y))
            r = max(10, min(200, r))

            # Оновлення даних гравця
            if conn in self.players:
                self.players[conn].update({
                    'x': x, 'y': y, 'r': r, 'name': name, 'last_update': time.time()
                })
            else:
                self.players[conn] = {
                    'id': pid, 'x': x, 'y': y, 'r': r, 'name': name, 'last_update': time.time()
                }
            
            return True

        except (ValueError, IndexError) as e:
            print(f"Помилка обробки даних: {e}, дані: {data}")
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

                # Перевірка поглинання (більш м'яка умова)
                collision_distance = (p1['r'] + p2['r']) * 0.7
                
                if distance < collision_distance:
                    if p1['r'] > p2['r'] * 1.2:  # Потрібна значна різниця для поглинання
                        p1['r'] += int(p2['r'] * 0.3)
                        self.players[conn1] = p1
                        eliminated.add(conn2)
                        print(f"Гравець {p1['name']} поглинув {p2['name']}")
                    elif p2['r'] > p1['r'] * 1.2:
                        p2['r'] += int(p1['r'] * 0.3)
                        self.players[conn2] = p2
                        eliminated.add(conn1)
                        print(f"Гравець {p2['name']} поглинув {p1['name']}")

        return eliminated

    def broadcast_game_state(self, eliminated):
        """Розсилка стану гри всім клієнтам"""
        to_remove = []
        active_players = {conn: player for conn, player in self.players.items() 
                         if conn not in eliminated}
        
        print(f"Активних гравців: {len(active_players)}")

        # Спочатку обробляємо програших
        for conn in eliminated:
            try:
                conn.send("LOSE".encode())
                print(f"Відправлено LOSE гравцю {self.players.get(conn, {}).get('name', 'Unknown')}")
            except:
                pass
            to_remove.append(conn)

        # Потім відправляємо дані активним гравцям
        for conn, player in list(active_players.items()):
            try:
                # Формування списку інших гравців (без себе)
                other_players = []
                for other_conn, other_player in active_players.items():
                    if other_conn != conn:
                        other_players.append(
                            f"{other_player['id']},{other_player['x']},{other_player['y']},"
                            f"{other_player['r']},{other_player['name']}"
                        )
                
                # Формування пакету
                if other_players:
                    packet = '|'.join(other_players) + '|'
                else:
                    packet = '|'  # Пустий пакет, якщо немає інших гравців
                
                conn.send(packet.encode())
                
            except (ConnectionResetError, BrokenPipeError, OSError) as e:
                print(f"З'єднання розірвано з {player.get('name', 'Unknown')}: {e}")
                to_remove.append(conn)
            except Exception as e:
                print(f"Помилка при відправці даних до {player.get('name', 'Unknown')}: {e}")
                to_remove.append(conn)

        # Видалення відключених клієнтів
        for conn in to_remove:
            player_name = self.players.get(conn, {}).get('name', 'Unknown')
            self.players.pop(conn, None)
            print(f"Видалено гравця: {player_name}")
            try:
                conn.close()
            except:
                pass

    def cleanup_inactive_players(self):
        """Видалення неактивних гравців"""
        current_time = time.time()
        to_remove = []
        
        for conn, player in self.players.items():
            if current_time - player.get('last_update', current_time) > 30:  # 30 секунд таймаут
                to_remove.append(conn)
        
        for conn in to_remove:
            player_name = self.players.get(conn, {}).get('name', 'Unknown')
            print(f"Видалено неактивного гравця: {player_name}")
            self.players.pop(conn, None)
            try:
                conn.close()
            except:
                pass

    def game_loop(self):
        """Основний ігровий цикл"""
        last_cleanup = time.time()
        
        while self.running:
            try:
                # Збір даних від клієнтів
                to_remove = []
                for conn in list(self.players.keys()):
                    try:
                        ready, _, _ = select.select([conn], [], [], 0)
                        if ready:
                            data = conn.recv(1024).decode().strip()
                            if data:
                                if not self.handle_client_data(conn, data):
                                    to_remove.append(conn)
                            else:
                                # Клієнт відключився
                                to_remove.append(conn)
                    except (ConnectionResetError, OSError):
                        to_remove.append(conn)
                    except Exception as e:
                        print(f"Помилка при читанні даних: {e}")
                        to_remove.append(conn)

                # Видалення проблемних з'єднань
                for conn in to_remove:
                    player_name = self.players.get(conn, {}).get('name', 'Unknown')
                    print(f"Видалено проблемне з'єднання: {player_name}")
                    self.players.pop(conn, None)

                # Обробка зіткнень
                eliminated = self.handle_collisions()

                # Розсилка оновлень
                self.broadcast_game_state(eliminated)
                
                # Очищення неактивних гравців раз на хвилину
                if time.time() - last_cleanup > 60:
                    self.cleanup_inactive_players()
                    last_cleanup = time.time()

                time.sleep(1 / 30)  # 30 FPS для сервера
                
            except Exception as e:
                print(f"Помилка в ігровому циклі: {e}")
                time.sleep(0.1)

    def accept_connections(self):
        """Прийом нових підключень"""
        while self.running:
            try:
                ready, _, _ = select.select([self.sock], [], [], 0.1)
                if ready:
                    conn, addr = self.sock.accept()
                    conn.setblocking(False)

                    self.id_counter += 1
                    
                    # Ініціалізація нового гравця
                    initial_player = {
                        'id': self.id_counter, 
                        'x': 0, 
                        'y': 0, 
                        'r': 20, 
                        'name': f'Player{self.id_counter}',
                        'last_update': time.time()
                    }
                    
                    self.players[conn] = initial_player

                    # Відправка початкових даних клієнту
                    init_data = f"{self.id_counter},0,0,20"
                    conn.send(init_data.encode())
                    
                    print(f"Новий гравець підключився: {addr}, ID: {self.id_counter}")
                    print(f"Всього гравців: {len(self.players)}")

            except Exception as e:
                print(f"Помилка при прийомі підключення: {e}")
                time.sleep(0.1)

    def start(self):
        """Запуск сервера"""
        print("Запуск ігрового сервера...")

        # Запуск потоків
        game_thread = Thread(target=self.game_loop, daemon=True)
        accept_thread = Thread(target=self.accept_connections, daemon=True)

        game_thread.start()
        accept_thread.start()

        try:
            while self.running:
                # Виведення статистики кожні 30 секунд
                print(f"Статус сервера: {len(self.players)} активних гравців")
                time.sleep(30)
        except KeyboardInterrupt:
            print("\nЗавершення роботи сервера...")
            self.running = False
            self.sock.close()


if __name__ == "__main__":
    server = GameServer()
    server.start()