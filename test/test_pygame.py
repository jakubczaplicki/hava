import os
import pygame
from datetime import datetime
import time

os.putenv('DISPLAY', ':0')
pygame.init()
lcd = pygame.display.set_mode((480, 320))
pygame.display.toggle_fullscreen()
font_small = pygame.font.SysFont("freemono", 25)
font_medium = pygame.font.SysFont("freemono", 32)
font_medium2 = pygame.font.SysFont("freemono", 35)
font_big = pygame.font.SysFont("freemono", 50)


def screen():
    timestamp = int(time.time())
    d = datetime.fromtimestamp(timestamp).strftime("%d-%m-%y %H:%M:%S")
    lcd.fill((0, 0, 0))
    text_surface_name = font_medium.render('Stowarzyszenie Pracownia', True, (200, 200, 200))
    text_surface_def1 = font_small.render('Mobilna stacja pomiaru', True, (200, 200, 200))
    text_surface_def2 = font_small.render('pyłu zawieszonego.', True, (200, 200, 200))
    text_surface_pm25 = font_big.render('PM2.5: {:.2f} µm'.format(3.14), True, (255, 255, 255))
    text_surface_pm10 = font_big.render('PM1.0: {:.2f} µm'.format(10.45), True, (255, 255, 255))
    text_surface_date = font_medium2.render('%s' % d, True, (255, 255, 255))
    lcd.blit(text_surface_name, (7, 8))
    lcd.blit(text_surface_def1, (5, 60))
    lcd.blit(text_surface_def2, (5, 90))
    lcd.blit(text_surface_pm25, (10, 160))
    lcd.blit(text_surface_pm10, (10, 210))
    lcd.blit(text_surface_date, (10, 270))
    img = pygame.image.load('logo.png')
    img = pygame.transform.scale(img, (150, 150))
    lcd.blit(img, (480-150, 30))
    pygame.display.update()


while True:
    screen()
    time.sleep(1)
    for event in pygame.event.get():
        if event.type == 12:
            pygame.quit()
