from pygame import*

init()

size = 1000, 700
window = display.set_mode(size)
clock = time.Clock()


class Block:
    def __init__(self, img_path, width, height):
        global blocks
        self.image = transform.scale(image.load(img_path), (width, height))
        self.width = width
        self.height = height
        self.rect = self.image.get_rect()
        self.rect.x = 0
        self.rect.y = 0
        blocks.append(self)

    def reset(self):
        window.blit(self.image, (self.rect.x, self.rect.y))
        #draw.rect(window, (255, 0, 0), self.rect, 2)


blocks = []
big_rock = Block('asset_level/big_rock.png', 150, 150)
medium_rock = Block('asset_level/medium_rock.png', 150, 100)
for i in range(5):
    Block('asset_level/full_g_block.png', 200, 60)
for i in range(5):
    Block('asset_level/full_h_block.png', 60, 200)
for i in range(5):
    Block('asset_level/one_block.png', 60, 60)
for i in range(5):
    Block('asset_level/little_bush.png', 60, 60)
for i in range(5):
    Block('asset_level/little_leaf.png', 60, 60)
for i in range(5):
    Block('asset_level/sprout_2.png', 60, 60)
for i in range(2):
    Block('asset_level/big_stick.png', 150, 250)

selected_block = None
offset_x, offset_y = 0, 0

while True:
    for e in event.get():
        if e.type == QUIT:
            quit()

        if e.type == MOUSEBUTTONDOWN:
            x, y = e.pos
            for block in blocks:
                if block.rect.collidepoint(x, y):
                    selected_block = block

                    offset_x = x - block.rect.x
                    offset_y = y - block.rect.y
                    break

        if e.type == MOUSEBUTTONUP:
            selected_block = None

        if e.type == MOUSEMOTION and selected_block:
            x, y = e.pos
            selected_block.rect.x = x - offset_x
            selected_block.rect.y = y - offset_y

    window.fill((0, 0, 0))

    for block in blocks:
        block.reset()

    display.update()
    clock.tick(60)
