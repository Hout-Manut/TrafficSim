import os
import time

import pygame

import simulation

RANDOMLY_ADD_CARS = pygame.USEREVENT + 1
TIME_CONTROL = pygame.USEREVENT + 2

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

def main(sim: simulation.Simulator):

    pygame.time.set_timer(RANDOMLY_ADD_CARS, 1000)
    pygame.time.set_timer(TIME_CONTROL, 14)

    sim.start()
    time_updated = 0
    while sim.running:
        clock.tick(FPS)
        check_events(sim)

        window.fill((255, 255, 255))

        # if time.time() - time_updated >= 0.5:

        sim.needs_refresh = True

        sim.draw_boundaries()


        draw_fps(sim)

        pygame.display.update()


def check_events(sim: simulation.Simulator):
      for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sim.stop()
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
                if sim.state == simulation.State.MENU:
                    sim.stop()
                    pygame.quit()
                    exit()
                else:
                    sim.go_to_menu()
            elif event.key == pygame.K_F11:
                sim.toggle_fullscreen()
        elif event.type == RANDOMLY_ADD_CARS:
            sim.randomly_add_cars()
        elif event.type == TIME_CONTROL:
            sim.update()


def draw_fps(sim: simulation.Simulator):
    fps_counter = str(int(clock.get_fps()))
    font = pygame.font.Font(os.path.join("Assets", "Mada-Medium.ttf"), 24)
    fps_text = font.render(fps_counter, True, simulation.Color.BLACK)
    rec = window.blit(fps_text, (9, sim.height - 30))


if __name__ == "__main__":
    is_fullscreen = False
    sim = simulation.Simulator(window, device_info, is_fullscreen, flags)
    main(sim)
