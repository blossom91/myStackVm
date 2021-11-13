import threading
from typing import List
import pygame


def real_color_value_mapper():
    d = {
        '00': 0,
        '01': 85,
        '10': 170,
        '11': 255,
    }
    return d


def color_from_byte_value(byte_int):
    # todo 映射暂时没有逻辑
    byte = '{:08b}'.format(byte_int)
    r = real_color_value_mapper()[byte[:2]]
    g = real_color_value_mapper()[byte[2:4]]
    b = real_color_value_mapper()[byte[4:6]]
    a = real_color_value_mapper()[byte[6:]]
    return r, g, b, a


# 套路，不需要看
class Screen:
    def __init__(self, pixel_width, pixel_height, memory: List, start_index):
        self.running = True
        self.memory = memory
        self.pixel_width = pixel_width
        self.pixel_height = pixel_height
        self.start_index = start_index

        # 放大像素点成为一个矩形
        self.pixel_gain = 20

    def run(self):
        clock = pygame.time.Clock()
        fps = 500

        pw = self.pixel_width
        ph = self.pixel_height
        pg = self.pixel_gain
        screen_width, screen_height = pw * pg, ph * pg
        pg_screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption('Stack Machine')
        icon = pygame.image.load('img/gua.png')
        pygame.display.set_icon(icon)

        while self.running:
            self.output(pg_screen)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

            pygame.display.flip()
            clock.tick(fps)

    def update(self, memory: List):
        self.memory = memory

    def exit(self):
        self.running = False

    def output(self, screen):
        start = self.start_index
        w = self.pixel_width
        h = self.pixel_height
        g = self.pixel_gain

        for y in range(h):
            for x in range(w):
                if self.memory[start + y * w + x] != 0:
                    byte_value = self.memory[start + y * w + x]
                    color = color_from_byte_value(byte_value)
                    pygame.draw.rect(screen, color, ((x * g, y * g), (g, g)), 0)

        pygame.display.flip()
        clock = pygame.time.Clock()
        clock.tick(24)
