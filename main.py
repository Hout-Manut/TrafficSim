import os
import time

import pygame

from simulation import Color, Simulator, UIElement, Text, Button, State

RANDOMLY_ADD_CARS = pygame.USEREVENT + 1
REFRESH = pygame.USEREVENT + 2

HD = 1280, 720
FHD = 1920, 1080
FHD_PLUS = 1920, 1200
QHD = 2560, 1440

WIDTH, HEIGHT = FHD
FPS = 1000
flags = pygame.RESIZABLE
pygame.init()
device_info = pygame.display.Info()
window = pygame.display.set_mode((WIDTH, HEIGHT), flags=flags)
pygame.display.set_caption("Traffic Simulator")
clock = pygame.time.Clock()

def main(sim: Simulator):

    pygame.time.set_timer(RANDOMLY_ADD_CARS, 1000)
    pygame.time.set_timer(REFRESH, 2000)
    sim.pause()
    draw_fps(sim)
    sim.needs_refresh = True
    load_components(sim)

    while sim.running:
        dt = clock.tick(FPS) / 1000
        sim.dt = dt
        check_events(sim)

        # if time.time() - time_updated >= 0.5:
        window.fill(Color.WHITE)

        sim.draw()
        sim.draw_debug()
        sim.update()
        sim.move()

        draw_fps(sim)

        if sim.needs_refresh:
            window.fill(Color.WHITE)
        sim.needs_refresh = False
        pygame.display.update()


def load_components(sim: Simulator):
    base_font = pygame.font.Font(
        os.path.join("Assets", "Roboto-Light.ttf"), 24)
    speed_text = Text(sim,
                      anchor=UIElement.TOP_L,
                      color=Color.BLACK,
                      font=base_font,
                      text=lambda sim: f"Speed: {sim.speed_str}",
                      layer=UIElement.FOREGROUND,
                      dynamic=True
                      )
    speed_text.load()
    base_font = pygame.font.Font(
        os.path.join("Assets", "Roboto-Light.ttf"), 20)
    speed_inc_button = Button(sim,
                              anchor=UIElement.TOP_L,
                              offset=(0, 50),
                              color=Color.CYAN,
                              font=base_font,
                              text="+ Speed",
                              width=100,
                              height=30,
                              layer=UIElement.FOREGROUND,
                              border_radius=5,
                              action=lambda sim: sim.increase_speed()
                              )
    speed_inc_button.load()
    pause_button = Button(sim,
                          anchor=UIElement.TOP_L,
                          offset=(110, 50),
                          color=Color.CYAN,
                          font=base_font,
                          text="Pause",
                          width=100,
                          height=30,
                          layer=UIElement.FOREGROUND,
                          border_radius=5,
                          action=lambda sim: sim.pause()
                          )
    pause_button.load()
    speed_dec_button = Button(sim,
                              anchor=UIElement.TOP_L,
                              offset=(220, 50),
                              color=Color.CYAN,
                              font=base_font,
                              text="- Speed",
                              width=100,
                              height=30,
                              layer=UIElement.FOREGROUND,
                              border_radius=5,
                              action=lambda sim: sim.decrease_speed()
                              )
    speed_dec_button.load()


def check_events(sim: Simulator):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        elif event.type == pygame.VIDEORESIZE:
            # Check if the new size is below the minimum size
            sim.needs_refresh = True
            new_width = max(event.w, HD[0])
            new_height = max(event.h, HD[1])

            # Only resize if necessary
            if new_width != event.w or new_height != event.h:
                pygame.display.set_mode(
                    (new_width, new_height), pygame.RESIZABLE)
            else:
                pygame.display.set_mode(
                    (event.w, event.h), pygame.RESIZABLE)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if sim.state == State.MENU:
                    sim.stop()
                    pygame.quit()
                    exit()
                else:
                    sim.go_to_menu()
            elif event.key == pygame.K_F11:
                sim.toggle_fullscreen()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                sim.handle_button_press(event)
        elif event.type == RANDOMLY_ADD_CARS:
            if not sim.paused:
                sim.randomly_add_cars()


def draw_fps(sim: Simulator):
    fps_counter = str(int(clock.get_fps()))
    font = pygame.font.Font(os.path.join("Assets", "Mada-Medium.ttf"), 24)
    fps_text = font.render(fps_counter, True, Color.BLACK)
    fps_rect = fps_text.get_rect()
    fps_rect.bottomleft = (9, HEIGHT - 30)
    window.fill(Color.WHITE, fps_rect)
    window.blit(fps_text, (9, sim.height - 30))


if __name__ == "__main__":
    is_fullscreen = False
    sim = Simulator(window, device_info, is_fullscreen, RANDOMLY_ADD_CARS)
    main(sim)
