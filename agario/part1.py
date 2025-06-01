from math import hypot
from pygame import *
from random import randint

my_player = [0, 0, 20]

init()
window = display.set_mode((1000, 1000))
clock = time.Clock()
f = font.Font(None, 50)
all_players = []
lose = False


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
running = True
while running:
   for e in event.get():
       if e.type == QUIT:
           running = False

   window.fill((255, 255, 255))
   scale = max(0.3, min(50 / my_player[2], 1.5))
   draw.circle(window, (0, 255, 0), (500, 500), int(my_player[2] * scale))

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
   keys = key.get_pressed()
   if keys[K_w]: my_player[1] -= 15
   if keys[K_s]: my_player[1] += 15
   if keys[K_a]: my_player[0] -= 15
   if keys[K_d]: my_player[0] += 15
   display.update()
   clock.tick(60)




quit()
