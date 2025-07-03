from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread
import time

sock = socket(AF_INET, SOCK_STREAM)
sock.bind(('localhost', 8081))
sock.listen(5)
sock.setblocking(False)

players = {}
conn_ids = {}
id_counter = 0


def handle_data():
    global id_counter
    while True:
        time.sleep(0.01)
        player_data = {}
        to_remove = []

        for conn in list(players):
            try:
                data = conn.recv(64).decode().strip()
                if ',' in data:
                    parts = data.split(',')
                    if len(parts) == 5:
                        try:
                            pid, x, y, r = map(int, parts[:4])
                            name = parts[-1]
                            players[conn] = {'id': pid, 'x': x, 'y': y, 'r': r, 'name': name}
                            player_data[conn] = players[conn]
                        except ValueError:
                            print(f"Invalid data format: {data}")
                            continue
            except Exception as e:
                continue

        eliminated = []
        for conn1 in player_data:
            if conn1 in eliminated:
                continue
            p1 = player_data[conn1]
            for conn2 in player_data:
                if conn1 == conn2 or conn2 in eliminated:
                    continue
                p2 = player_data[conn2]
                dx, dy = p1['x'] - p2['x'], p1['y'] - p2['y']
                distance = (dx ** 2 + dy ** 2) ** 0.5
                if distance < p1['r'] + p2['r'] and p1['r'] > p2['r'] * 1.1:
                    p1['r'] += int(p2['r'] * 0.5)
                    players[conn1] = p1
                    eliminated.append(conn2)

        for conn in list(players.keys()):
            if conn in eliminated:
                try:
                    conn.send("LOSE".encode())
                except:
                    pass
                to_remove.append(conn)
                continue

            try:
                # Виправлено: тільки надсилаємо дані інших гравців
                other_players = [p for c, p in players.items() if c != conn and c not in eliminated]
                if other_players:
                    packet = '|'.join([f"{p['id']},{p['x']},{p['y']},{p['r']},{p['name']}"
                                       for p in other_players]) + '|'
                else:
                    packet = '|'
                conn.send(packet.encode())
            except Exception as e:
                print(f"Error sending data to client: {e}")
                to_remove.append(conn)

        for conn in to_remove:
            if conn in players:
                print(f"Removing player {players[conn]['id']}")
                players.pop(conn, None)
                conn_ids.pop(conn, None)
                try:
                    conn.close()
                except:
                    pass


Thread(target=handle_data, daemon=True).start()
print("SERVER running on localhost:8081...")

while True:
    try:
        conn, addr = sock.accept()
        conn.setblocking(False)
        id_counter += 1
        players[conn] = {'id': id_counter, 'x': 0, 'y': 0, 'r': 20, 'name': f'Player{id_counter}'}
        conn_ids[conn] = id_counter

        # Виправлено: надсилаємо початкові дані в правильному форматі
        initial_data = f"{id_counter},0,0,20"
        conn.send(initial_data.encode())
        print(f"New player connected: ID {id_counter}, sent: {initial_data}")
    except Exception as e:
        pass