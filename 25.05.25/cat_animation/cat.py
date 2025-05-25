from pygame import *
from random import randint

init()

window = display.set_mode((1000, 800))
clock = time.Clock()


class Player:
   def __init__(self, x, y, width, height, images):
       self.images = [transform.scale(image.load(img), (width, height)) for img in images]
       self.frame_index = 0
       self.image_speed = 0.05  # Швидкість анімації
       self.rect = self.images[0].get_rect(topleft=(x, y))
       self.current_img = self.images[0]

   def reset(self):
       window.blit(self.current_img, (self.rect.x, self.rect.y))

   def animate(self):
       self.frame_index += self.image_speed
       if self.frame_index >= len(self.images):
           self.frame_index = 0
       self.current_img = self.images[int(self.frame_index)]


player_run = [f'{i}.png' for i in range(1, 3)]
player = Player(400, 150, 180, 200, player_run)
btn_rect = Rect(500-350//2, 350, 350, 100)
f = font.Font('Howdy Duck.otf', 40)
play_text = f.render('PLay', 1, (200, 200, 220))
wait = 0
while True:
   for e in event.get():
       if e.type == QUIT:
           quit()

   window.fill((220, 230, 230))
   player.animate()
   player.reset()
   if wait == 0:
       r = randint(0, 255)
       g = randint(0, 255)
       b = randint(0, 255)
       wait = 20
   else:
       wait -= 1

   draw.rect(window, (r, g, b), btn_rect, border_radius=15)
   draw.rect(window, (200, 200, 200), [btn_rect.x, btn_rect.y, btn_rect.w, btn_rect.h], 6, border_radius=15)
   window.blit(play_text, (btn_rect.x+120, btn_rect.y+20))
   display.update()
   clock.tick(60)

