from __future__ import annotations

import math
import os
import random
import time
from abc import abstractmethod
from typing import Callable, Optional

import numpy as np
import pygame

from .utills import ease, lerp
from . import trafficlight

RANDOMLY_ADD_CARS = pygame.USEREVENT + 1


class Simulator:

    def __init__(self,
                 window: pygame.Surface,
                 device_info,
                 is_fullscreen,
                 user_event_1: int,
                 ) -> None:
        self.window = window
        self.resolution = (self.window.get_width(), self.window.get_height())
        self.device_info = device_info
        self.is_fullscreen = is_fullscreen
        self.running = True
        self.time_started = time.time()
        self.time_speed: float = 1.0
        self.randomly_add_cars_event = user_event_1

        self.view_1 = ViewLeft(self)
        self.view_2 = ViewRight(self)

        self.hide_hud = False

        self.road_spawn_rate = [
            1.0,
            1.0,
            1.0,
            1.0,
            ]

        self.light_1 = None
        self.light_2 = None

        self.needs_refresh = True
        self.bg_elements: list[UIElement] = []
        self.mg_elements: list[UIElement] = []
        self.fg_elements: list[UIElement] = []
        self.buttons: list[Button] = []
        self.paused = False
        self.dt = 0.0
        self.base_spawn_rate = 1000
        self.multiplier = 1

        pygame.time.set_timer(RANDOMLY_ADD_CARS, self.base_spawn_rate)

        self.divider = pygame.image.load(os.path.join("Assets", "divider.png"))
        self.divider = pygame.transform.scale(
            self.divider, (self.divider.get_width(), self.window.get_height()))
        self.divider_rect = self.divider.get_rect()
        self.divider_rect.center = (
            self.window.get_width() / 2, self.window.get_height() / 2)

    def reset_all(self) -> None:
        del self.view_1
        del self.view_2

        self.view_1 = ViewLeft(self)
        self.view_2 = ViewRight(self)

        self.needs_refresh = True

    @property
    def time(self) -> int:
        return int(time.time() - self.time_started)

    def reset_time(self) -> None:
        self.time_started = time.time()

    def reset(self) -> None:
        self.reset_time()
        self.view_1.reset_car_leaves()
        self.view_2.reset_car_leaves()

    @property
    def speed(self) -> float:
        return 0.0 if self.paused else self.time_speed

    @property
    def speed_str(self) -> str:
        return "Paused" if self.paused else f"{self.speed:.2f}x"

    @speed.setter
    def speed(self, value: float) -> None:
        self.time_speed = value

    def get_spawn_str(self, index) -> str:
        return f"{self.road_spawn_rate[index]:.2f}x"

    def load_smart_light(self,
                         max_value: float = 120,
                         base_offset: int = 30,
                         increment_value: float = 1.0,
                         no_traffic_multiplier: float = 5.0,
                         value_per_car: float = 1.0
                         ) -> None:
        self.light_1 = trafficlight.Smart(
            self, max_value, base_offset, increment_value, no_traffic_multiplier, value_per_car)

    def load_basic_light(self,
                         value=120.0
                         ) -> None:
        self.light_2 = trafficlight.Basic(self, value)

    def increase_speed(self) -> None:
        if self.paused:
            self.pause()
        self.time_speed = min(5.0, self.time_speed + 0.1)

    def decrease_speed(self) -> None:
        if self.paused:
            self.pause()
        self.time_speed = max(0.0, self.time_speed - 0.1)

    def get_active_road_cars(self, view_index=1) -> int:
        if view_index == 1:
            return self.view_1.get_all_active_road_cars()
        elif view_index == 2:
            return self.view_2.get_all_active_road_cars()

    def get_inactive_road_cars(self, view_index=1) -> int:
        if view_index == 1:
            return self.view_1.get_all_inactive_road_cars()
        elif view_index == 2:
            return self.view_2.get_all_inactive_road_cars()

    @property
    def rect(self) -> pygame.Rect:
        return self.window.get_rect()

    @property
    def dt(self) -> float:
        return self._dt

    @dt.setter
    def dt(self, value: float) -> None:
        self._dt = value

    @property
    def width(self) -> int:
        return self.window.get_width()

    @property
    def height(self) -> int:
        return self.window.get_height()

    def add_button(self, button: Button) -> None:
        self.buttons.append(button)

    def handle_button_press(self, event: pygame.event) -> None:
        for button in self.buttons:
            button.handle_event(event)

    def toggle_lights(self, view_index=0) -> None:
        if view_index == 0:
            self.view_1.toggle_lights()
            return
        elif view_index == 1:
            self.view_2.toggle_lights()
            return
        self.view_1.toggle_lights()
        self.view_2.toggle_lights()

    def toggle_light(self, index: int) -> None:
        if index == 1:
            self.light_1.toggle_light()
            return
        elif index == 2:
            self.light_2.toggle_light()
            return
        self.light_1.toggle_light()
        self.light_2.toggle_light()

    def pause(self) -> None:
        self.paused = not self.paused

    def spawn_multiplier(self) -> str:
        return f"{self.multiplier:.2f}x"

    def increase_spawn_rate(self, index: Optional[int] = None) -> None:
        if index is not None:
            self.road_spawn_rate[index] = min(2.0, self.road_spawn_rate[index] + 0.1)
        else:
            self.multiplier = min(5.0, self.multiplier + 0.1)
            pygame.time.set_timer(RANDOMLY_ADD_CARS, int(
                self.base_spawn_rate / self.multiplier))

    def decrease_spawn_rate(self, index: Optional[int] = None) -> None:
        if index is not None:
            self.road_spawn_rate[index] = max(0.1, self.road_spawn_rate[index] - 0.1)
        else:
            self.multiplier = max(0.1, self.multiplier - 0.1)
            pygame.time.set_timer(RANDOMLY_ADD_CARS, int(
                self.base_spawn_rate / self.multiplier))

    def randomly_add_cars(self, chance: Optional[int] = 50, road_index: Optional[int] = None) -> None:
        color = random.randint(1, 9)
        ran = random.randint(0, 120)
        direction = random.randint(0, 2)
        if road_index is None:
            road_index = random.randint(0, 3)
        if ran <= chance * self.road_spawn_rate[road_index]:
            self.view_1[road_index].add_car(direction, color)
            self.view_2[road_index].add_car(direction, color)

    def set_preset(self,
                   r1: Optional[float] = None,
                   r2: Optional[float] = None,
                   r3: Optional[float] = None,
                   r4: Optional[float] = None,
                   ) -> None:
        self.road_spawn_rate[0] = self.road_spawn_rate[0] if r1 is None else r1
        self.road_spawn_rate[1] = self.road_spawn_rate[1] if r2 is None else r2
        self.road_spawn_rate[2] = self.road_spawn_rate[2] if r3 is None else r3
        self.road_spawn_rate[3] = self.road_spawn_rate[3] if r4 is None else r4

    def draw_debug(self) -> None:
        self.view_1.draw_debug()
        self.view_2.draw_debug()

    def draw(self) -> None:
        self.view_1.draw()
        self.view_2.draw()
        if not self.hide_hud:
            for element in self.bg_elements:
                element.draw()
        self.view_1.draw_cars()
        self.view_2.draw_cars()
        self.window.blit(self.divider, self.divider_rect)
        if not self.hide_hud:
            for element in self.mg_elements:
                element.draw()
            for element in self.fg_elements:
                element.draw()
            for button in self.buttons:
                button.draw()

        self.needs_refresh = False

    def update(self) -> None:
        if self.needs_refresh:
            self.divider = pygame.transform.scale(
                self.divider, (self.divider.get_width(), self.view_1.road_top.road_width *3))
            self.divider_rect = self.divider.get_rect()
            self.divider_rect.center = (self.window.get_width() / 2,
                                        self.window.get_height() / 2)
        self.view_1.update()
        self.light_1.update()
        self.view_2.update()
        self.light_2.update()

    def move(self) -> None:
        self.view_1.move()
        self.view_2.move()

    def add_element(self, element: UIElement) -> None:
        if element.z == 0:
            self.bg_elements.append(element)
        elif element.z == 1:
            self.mg_elements.append(element)
        elif element.z == 2:
            self.fg_elements.append(element)


class View:

    rect: pygame.Rect

    def __init__(self, sim: Simulator) -> None:
        self.sim = sim

        self.road_top = RoadTop(self, 2)
        self.road_right = RoadRight(self, 0)
        self.road_bottom = RoadBottom(self, 2)
        self.road_left = RoadLeft(self, 0)

        self.cars = []
        self.car_leaves = 0

    def increment_car_leaves(self) -> None:
        self.car_leaves += 1

    def reset_car_leaves(self) -> None:
        self.car_leaves = 0

    def average_car_leaves(self) -> str:
        try:
            time_since_start = self.sim.time
            minutes = time_since_start / 60
            return f"{self.car_leaves / minutes:.2f}"
        except ZeroDivisionError:
            return "N/A"

    @property
    def width(self) -> int:
        return self.rect.width

    @property
    def height(self) -> int:
        return self.rect.height

    def update_cars(self) -> None:
        self.cars = self.road_top.cars + self.road_right.cars + \
            self.road_bottom.cars + self.road_left.cars
        if len(self.cars) > 30:
            self.road_top.car_spawn_distance = 500
            self.road_right.car_spawn_distance = 500
            self.road_bottom.car_spawn_distance = 500
            self.road_left.car_spawn_distance = 500
            self.road_top.update_lane()
            self.road_right.update_lane()
            self.road_bottom.update_lane()
            self.road_left.update_lane()
        elif len(self.cars) > 50:
            self.road_top.car_spawn_distance = 1000
            self.road_right.car_spawn_distance = 1000
            self.road_bottom.car_spawn_distance = 1000
            self.road_left.car_spawn_distance = 1000
            self.road_top.update_lane()
            self.road_right.update_lane()
            self.road_bottom.update_lane()
            self.road_left.update_lane()

    def get_all_cars(self) -> list[Car]:
        return self.cars

    def update(self) -> None:
        self.road_top.update()
        self.road_right.update()
        self.road_bottom.update()
        self.road_left.update()

    def move(self) -> None:
        self.road_top.move()
        self.road_right.move()
        self.road_bottom.move()
        self.road_left.move()

    def draw_debug(self) -> None:
        self.sim.window.set_clip(self.rect)
        self.road_top.draw_debug()
        self.road_right.draw_debug()
        self.road_bottom.draw_debug()
        self.road_left.draw_debug()
        self.sim.window.set_clip(None)

    def draw_cars(self) -> None:
        self.sim.window.set_clip(self.rect)
        self.road_top.draw_cars()
        self.road_right.draw_cars()
        self.road_bottom.draw_cars()
        self.road_left.draw_cars()
        self.sim.window.set_clip(None)

    def draw(self) -> None:
        self.sim.window.set_clip(self.rect)
        self.road_top.draw()
        self.road_right.draw()
        self.road_bottom.draw()
        self.road_left.draw()
        self.sim.window.set_clip(None)

    def toggle_lights(self) -> None:
        self.road_top.toggle_lights()
        self.road_right.toggle_lights()
        self.road_bottom.toggle_lights()
        self.road_left.toggle_lights()

    def toggle_top_lights(self) -> None:
        self.road_top.toggle_lights()

    def toggle_right_lights(self) -> None:
        self.road_right.toggle_lights()

    def toggle_bottom_lights(self) -> None:
        self.road_bottom.toggle_lights()

    def toggle_left_lights(self) -> None:
        self.road_left.toggle_lights()

    def get_all_active_road_cars(self) -> int:
        return sum([road.get_active_cars() for road in self])

    def get_all_inactive_road_cars(self) -> int:
        return sum([road.get_inactive_cars() for road in self])

    def __len__(self) -> int:
        return 4

    def __getitem__(self, index):
        if index == 0:
            return self.road_top
        if index == 1:
            return self.road_right
        if index == 2:
            return self.road_bottom
        if index == 3:
            return self.road_left
        raise IndexError


class ViewLeft(View):

    def __init__(self, sim: Simulator) -> None:
        self.rect = pygame.Rect(0, 0, sim.width // 2, sim.height)
        super().__init__(sim)

    def update(self) -> None:
        self.rect = pygame.Rect(0, 0, self.sim.width // 2, self.sim.height)
        super().update()


class ViewRight(View):

    def __init__(self, sim: Simulator) -> None:
        self.rect = pygame.Rect(sim.width // 2, 0, sim.width // 2, sim.height)
        super().__init__(sim)

    def update(self) -> None:
        self.rect = pygame.Rect(self.sim.width // 2, 0,
                                self.sim.width // 2, self.sim.height)
        super().update()


class Road:

    def __init__(self, view: View, light_state: int = 0) -> None:
        self.view = view
        self.car_spawn_distance = 100
        self.lane_left = LaneLeft(self)
        self.lane_straight = LaneStraight(self)
        self.lane_right = LaneRight(self)
        self.lanes = [self.lane_left, self.lane_straight, self.lane_right]
        self.rect = self.get_bound()
        self.light_rect = self.get_light_bound()
        self.cars: list[Car] = []
        self.light = TrafficLight(self, light_state)
        self.load_sprite()
        self.update_graphic()

    def load_sprite(self) -> None:
        self.center = pygame.image.load(
            os.path.join("Assets", "intersect.png")
        )
        self.zebras = [pygame.transform.rotate(pygame.image.load(
            os.path.join("Assets", "zebra.png")), 90 * i) for i in range(4)]
        self.sprite = pygame.image.load(
            os.path.join("Assets", "road.png")
        )

    @property
    def is_active(self) -> bool:
        return True if self.light.state == State.Light.GREEN else False

    def is_green(self) -> bool:
        return self.light.state == State.Light.GREEN or self.light.state == State.Light.PRE_GREEN

    def get_active_cars(self) -> int:
        if self.is_green():
            cars = self.get_half_bound().collidelistall(
                [car.rect for car in self.cars])
            return len(cars)
        return 0

    def get_inactive_cars(self) -> int:
        if not self.is_green():
            cars = self.get_half_bound().collidelistall(
                [car.rect for car in self.cars])
            return len(cars)
        return 0

    @property
    def state(self) -> bool:
        return self.light.state

    @state.setter
    def state(self, state: int) -> None:
        self.light.state = state

    @property
    def road_width(self) -> int:
        return int(self.view.rect.height * 0.1)

    @property
    def window(self) -> pygame.Surface:
        return self.view.sim.window

    def toggle_lights(self) -> None:
        self.light.toggle()

    def add_car(self, direction: int, color: int) -> None:
        new_car = Car(self.lanes[direction], color=color)
        self.cars.append(new_car)

    def update(self) -> None:
        if self.view.sim.needs_refresh:
            self.rect = self.get_bound()
            self.light_rect = self.get_light_bound()
            self.update_graphic()

        self.light.update()

        for car in self.cars:
            car.update()

    def move(self) -> None:
        for car in self.cars:
            car.move()

    def update_lane(self):
        for lane in self.lanes:
            lane.update()

    @abstractmethod
    def get_light_coords(self) -> tuple[int, int]:
        ...

    @abstractmethod
    def direction(self) -> int:
        ...

    @abstractmethod
    def get_half_bound(self) -> pygame.Rect:
        ...

    @abstractmethod
    def get_bound(self) -> pygame.Rect:
        ...

    @abstractmethod
    def get_light_bound(self) -> pygame.Rect:
        ...

    def draw_cars(self) -> None:
        for car in self.cars:
            car.draw()

    def draw_debug(self) -> None:
        pygame.draw.rect(self.window, self.color, self.get_half_bound(), 2)
        pygame.draw.rect(self.window, self.color, self.light_rect, 5)
        for car in self.cars:
            car.draw()

    def update_graphic(self):
        self.center = pygame.transform.scale(
            self.center, (self.road_width * 2, self.road_width * 2)
        )
        new_zebra = [pygame.transform.scale(
            zebra, (self.road_width * 2, self.road_width * 2)) for zebra in self.zebras]
        self.zebras = new_zebra
        self.sprite = pygame.transform.scale(
            self.sprite, (self.road_width * 2, self.road_width * 2)
        )
        sprite_1 = self.sprite
        sprite_2 = pygame.transform.rotate(self.sprite, 90)
        self.blit_list = []

        x = self.view.rect.width // 2 - self.road_width
        x += self.view.rect.x
        y = self.view.rect.height // 2 - self.road_width

        self.blit_list.append((self.center, (x, y)))

        x = self.view.rect.width // 2 - (self.road_width * 3)  # Left
        x += self.view.rect.x
        y = self.view.rect.height // 2 - self.road_width

        self.blit_list.append((self.zebras[0], (x, y)))

        x = self.view.rect.width // 2 + self.road_width  # Right
        x += self.view.rect.x

        self.blit_list.append((self.zebras[2], (x, y)))

        x = self.view.rect.width // 2 - self.road_width
        x += self.view.rect.x
        y = self.view.rect.height // 2 - (self.road_width * 3)  # Top

        self.blit_list.append((self.zebras[3], (x, y)))

        y = self.view.rect.height // 2 + self.road_width  # Bottom

        self.blit_list.append((self.zebras[1], (x, y)))

        times = self.view.rect.height // 2 - (self.road_width * 3)
        length = self.sprite.get_height()
        times = times // length + 1
        y = self.view.rect.height // 2 - (self.road_width * 5)
        y2 = self.view.rect.height // 2 + (self.road_width * 3)
        for i in range(times):
            to_blit = sprite_2, (x, y - i * length)
            self.blit_list.append(to_blit)
            to_blit = sprite_2, (x, y2 + i * length)
            self.blit_list.append(to_blit)

        x = self.view.rect.width // 2 - (self.road_width * 5)
        x += self.view.rect.x
        x2 = self.view.rect.width // 2 + (self.road_width * 3)
        x2 += self.view.rect.x
        y = self.view.rect.height // 2 - self.road_width
        for i in range(times):
            to_blit = sprite_1, (x - i * length, y)
            self.blit_list.append(to_blit)
            to_blit = sprite_1, (x2 + i * length, y)
            self.blit_list.append(to_blit)

    def draw(self) -> None:
        self.light.draw()


class RoadTop(Road):

    @property
    def color(self) -> tuple[int, int, int]:
        return Color.PURPLE

    @property
    def direction(self) -> int:
        return 0

    def get_half_bound(self) -> pygame.Rect:
        view = [self.view.rect.x, self.view.rect.y,
                self.view.rect.width, self.view.rect.height]
        x = view[2] // 2 - self.road_width + view[0]
        # y = 0
        y = -view[3] // 2
        w = self.road_width
        # h = view[3] // 2 - self.road_width
        h = view[3] - self.road_width
        return pygame.Rect(x, y, w, h)

    def get_bound(self) -> pygame.Rect:
        view = [self.view.rect.x, self.view.rect.y,
                self.view.rect.width, self.view.rect.height]
        x = view[2] // 2 - self.road_width + view[0]
        y = 0
        w = self.road_width
        h = view[3]
        return pygame.Rect(x, y, w, h)

    def get_light_bound(self) -> pygame.Rect:
        view = [self.view.rect.x, self.view.rect.y,
                self.view.rect.width, self.view.rect.height]
        x = view[2] // 2 - self.road_width + view[0]
        y = view[3] // 2 - self.road_width * 1.7
        w = self.road_width
        h = 5
        return pygame.Rect(x, y, w, h)

    def get_light_coords(self) -> tuple[int, int]:
        view = [self.view.rect.x, self.view.rect.y,
                self.view.rect.width, self.view.rect.height]
        x = view[2] // 2 - self.road_width - 40
        y = view[3] // 2 - self.road_width - 80
        x += view[0]
        return x, y

    def draw(self) -> None:
        if self.view.sim.needs_refresh:
            self.update_graphic()

        self.window.blits(self.blit_list)
        self.light.draw()


class RoadRight(Road):

    @property
    def color(self) -> tuple[int, int, int]:
        return Color.RED

    def get_half_bound(self) -> pygame.Rect:
        view = [self.view.rect.x, self.view.rect.y,
                self.view.rect.width, self.view.rect.height]
        x = view[2] // 2 + self.road_width + view[0]
        y = view[3] // 2 - self.road_width
        # w = view[2] // 2 - self.road_width
        w = view[2] - self.road_width
        h = self.road_width
        return pygame.Rect(x, y, w, h)

    def get_bound(self) -> pygame.Rect:
        view = [self.view.rect.x, self.view.rect.y,
                self.view.rect.width, self.view.rect.height]
        x = 0 + view[0]
        y = view[3] // 2 - self.road_width
        w = view[2]
        h = self.road_width
        return pygame.Rect(x, y, w, h)

    def get_light_bound(self) -> pygame.Rect:
        view = [self.view.rect.x, self.view.rect.y,
                self.view.rect.width, self.view.rect.height]
        x = view[2] // 2 + (self.road_width * 1.7) + view[0]
        y = view[3] // 2 - self.road_width
        w = 5
        h = self.road_width
        return pygame.Rect(x, y, w, h)

    def get_light_coords(self) -> tuple[int, int]:
        view = [self.view.rect.x, self.view.rect.y,
                self.view.rect.width, self.view.rect.height]
        x = view[2] // 2 + self.road_width + 40
        y = view[3] // 2 - self.road_width - 80
        x += view[0]
        return x, y

    @property
    def direction(self) -> int:
        return 1


class RoadBottom(Road):
    @property
    def color(self) -> tuple[int, int, int]:
        return Color.BLUE

    def get_half_bound(self) -> pygame.Rect:
        view = [self.view.rect.x, self.view.rect.y,
                self.view.rect.width, self.view.rect.height]
        x = view[2] // 2 + view[0]
        y = view[3] // 2 + self.road_width
        w = self.road_width
        # h = view[3] // 2 - self.road_width
        h = view[3] - self.road_width
        return pygame.Rect(x, y, w, h)

    def get_bound(self) -> pygame.Rect:
        view = [self.view.rect.x, self.view.rect.y,
                self.view.rect.width, self.view.rect.height]
        x = (view[2] // 2) + view[0]
        y = 0
        w = self.road_width
        h = view[3]
        return pygame.Rect(x, y, w, h)

    def get_light_bound(self) -> pygame.Rect:
        view = [self.view.rect.x, self.view.rect.y,
                self.view.rect.width, self.view.rect.height]
        x = (view[2] // 2) + view[0]
        y = view[3] // 2 + self.road_width * 1.7
        w = self.road_width
        h = 5
        return pygame.Rect(x, y, w, h)

    def get_light_coords(self) -> tuple[int, int]:
        view = [self.view.rect.x, self.view.rect.y,
                self.view.rect.width, self.view.rect.height]
        x = view[2] // 2 + self.road_width + 40
        y = view[3] // 2 + self.road_width + 40
        x += view[0]
        return x, y

    @property
    def direction(self) -> int:
        return 2


class RoadLeft(Road):

    @property
    def color(self) -> tuple[int, int, int]:
        return Color.BLACK

    def get_half_bound(self) -> pygame.Rect:
        view = [self.view.rect.x, self.view.rect.y,
                self.view.rect.width, self.view.rect.height]
        # x = 0 + view[0]
        x = view[2] // 2 + view[0]
        y = view[3] // 2
        # w = view[2] // 2 - self.road_width
        w = view[2] - self.road_width
        h = self.road_width
        return pygame.Rect(x, y, w, h)

    def get_bound(self) -> pygame.Rect:
        view = [self.view.rect.x, self.view.rect.y,
                self.view.rect.width, self.view.rect.height]
        x = 0 + view[0]
        y = view[3] // 2
        w = view[2]
        h = self.road_width
        return pygame.Rect(x, y, w, h)

    def get_light_bound(self) -> pygame.Rect:
        view = [self.view.rect.x, self.view.rect.y,
                self.view.rect.width, self.view.rect.height]
        x = view[2] // 2 - (self.road_width * 1.7) + view[0]
        y = view[3] // 2
        w = 5
        h = self.road_width
        return pygame.Rect(x, y, w, h)

    def get_light_coords(self) -> tuple[int, int]:
        view = [self.view.rect.x, self.view.rect.y,
                self.view.rect.width, self.view.rect.height]
        x = view[2] // 2 - self.road_width - 40
        y = view[3] // 2 + self.road_width + 40
        x += view[0]
        return x, y

    @property
    def direction(self) -> int:
        return 3


class Lane:

    def __init__(self, road: Road) -> None:
        self.road = road
        self.view = road.view
        self._car_spawn = self.get_car_spawn()

    def get_car_spawn(self) -> tuple[int, int]:
        view = [self.view.rect.x, self.view.rect.y,
                self.view.rect.width, self.view.rect.height]
        distance = self.road.car_spawn_distance
        if isinstance(self.road, RoadTop):
            x = (view[2] // 2 - self.road.road_width * 0.8) + view[0]
            y = -distance
        elif isinstance(self.road, RoadRight):
            x = (view[2] + distance) + view[0]
            y = view[3] // 2 - self.road.road_width * 0.8
        elif isinstance(self.road, RoadBottom):
            x = (view[2] // 2 + self.road.road_width * 0.6) + view[0]
            y = view[3] + distance
        else:
            x = -distance + view[0]
            y = view[3] // 2 + self.road.road_width * 0.6
        return (x, y)

    @property
    def car_spawn(self) -> tuple[int, int]:
        return self._car_spawn

    @property
    def width(self) -> int:
        return self.road.road_width // 4

    def update(self) -> None:
        self._car_spawn = self.get_car_spawn()


class LaneLeft(Lane):

    def get_car_spawn(self) -> tuple[int, int]:
        view = [self.view.rect.x, self.view.rect.y,
                self.view.rect.width, self.view.rect.height]
        if isinstance(self.road, RoadTop):
            x = (view[2] // 2 - self.road.road_width // 3) + view[0]
            y = -100
        elif isinstance(self.road, RoadRight):
            x = (view[2] + 100) + view[0]
            y = view[3] // 2 - self.road.road_width // 3
        elif isinstance(self.road, RoadBottom):
            x = (view[2] // 2 + self.road.road_width * 0.2) + view[0]
            y = view[3] + 100
        else:
            x = -100 + view[0]
            y = view[3] // 2 + self.road.road_width * 0.2
        return (x, y)

    @property
    def direction(self) -> int:
        return self.LEFT


class LaneStraight(Lane):

    @property
    def direction(self) -> int:
        return self.STRAIGHT


class LaneRight(Lane):

    @property
    def direction(self) -> int:
        return self.RIGHT


class Car:

    BASE_SPEED = 200.0
    BASE_ACCEL = 100.0

    ACCELERATING = 1
    DECELERATING = 2
    TURN_LEFT = 3
    TURN_RIGHT = 4

    def __init__(self,
                 lane: Lane,
                 *,
                 accel: Optional[float] = None,
                 color: Optional[int] = None,
                 speed: Optional[float] = None,
                 ) -> None:
        self.lane = lane
        self.road = lane.road
        self.size = (30, 30)

        if not color:
            self.color = random.randint(1, 9)
        else:
            self.color = color

        self.load_sprites()

        self.old_view_rect = lane.view.rect.width, lane.view.rect.height
        r_modifier = random.random()
        self._speed = speed or Car.BASE_SPEED + r_modifier
        r_modifier = random.random()
        self.accel = accel or Car.BASE_ACCEL + r_modifier
        x, y = lane.car_spawn
        ran = [random.uniform(-2, 2), random.uniform(-2, 2)]
        x = x + ran[0]
        y = y + ran[1]
        self.rect = pygame.Rect(x, y, self.size[0], self.size[1])
        self.x = x
        self.y = y

        self.state = Car.ACCELERATING
        self.time = time.time()

        self.velocity: list[float] = [0, 0]
        road_dir = lane.road.direction
        ran = random.randint(0, 3)
        ran += 1
        self.is_turning = False
        self.turn_progress = 0.0
        self.turn_speed = 1
        self.speed_2 = self.speed / 2
        self.turned = False
        self.turn_time = 0.0
        self.turn_rate = 90
        if road_dir == 0:

            self.ori_orientation = 90  # Road from the top, car faces down
            self.left = lane.road.view.road_right
            self.right = lane.road.view.road_left
            self.opposite = lane.road.view.road_bottom
            self.offset = 0, self.size[0] + ran
            self.lookahead = pygame.Rect(
                x, y + self.offset[1], self.size[0], self.size[1] * 2)
        elif road_dir == 1:

            self.ori_orientation = 180  # Road from the right, car faces left
            self.left = lane.road.view.road_bottom
            self.right = lane.road.view.road_top
            self.opposite = lane.road.view.road_left
            self.offset = -(self.size[0] * 2 + ran), 0
            self.lookahead = pygame.Rect(
                x + self.offset[0], y, self.size[0] * 2, self.size[1])
        elif road_dir == 2:

            self.ori_orientation = 270  # Road from the bottom, car faces up
            self.left = lane.road.view.road_left
            self.right = lane.road.view.road_right
            self.opposite = lane.road.view.road_top
            self.offset = 0, -(self.size[0] * 2 + ran)
            self.lookahead = pygame.Rect(
                x, y + self.offset[1], self.size[0], self.size[1] * 2)
        else:

            self.ori_orientation = 0  # Road from the left, car faces right
            self.left = lane.road.view.road_top
            self.right = lane.road.view.road_bottom
            self.opposite = lane.road.view.road_right
            self.offset = self.size[0] + ran, 0
            self.lookahead = pygame.Rect(
                x + self.offset[0], y, self.size[0] * 2, self.size[1])

        self.orientation = self.ori_orientation

    @property
    def speed(self) -> float:
        return self._speed * self.simulator.speed

    @property
    def view(self) -> View:
        return self.lane.view

    @property
    def simulator(self) -> Simulator:
        return self.lane.road.view.sim

    @property
    def direction(self) -> int:
        return self.lane.direction

    def check(self) -> None:
        cars = self.road.view.get_all_cars()
        car_rects = [car.rect for car in cars if car is not self]
        oppo_cars = self.opposite.cars
        left_cars = self.left.cars
        right_cars = self.right.cars

        if self.turned:
            self.accelerate()
            return

        # if math.hypot(self.velocity[0], self.velocity[1]) < 0.01:
        #     self.accelerate()
        #     return

        if self.lookahead.colliderect(self.road.get_light_bound()):
            if not self.road.is_active:
                self.decelerate()
                return
            elif self.lookahead.collidelist(car_rects) != -1:
                self.decelerate()
                return
            elif self.road.get_bound().collidelist(right_cars) != -1:
                self.decelerate()
                return
            if self.lookahead.colliderect(self.left.rect):
                car_index = self.opposite.get_bound().collidelist(left_cars)
                if car_index != -1:
                    if self.left.get_bound().colliderect(left_cars[car_index]):
                        self.decelerate()
                        return

        if isinstance(self.lane, LaneLeft):
            if isinstance(self.road, RoadTop) or isinstance(self.road, RoadLeft):
                if self.rect.colliderect(self.road.get_bound()):
                    if self.lookahead.colliderect(self.left.get_bound()):
                        car_indexes = self.opposite.get_bound().collidelistall(oppo_cars)
                        for i in car_indexes:
                            car = oppo_cars[i]
                            if isinstance(oppo_cars[i].lane, LaneLeft):
                                if abs(car.x - car.lane.car_spawn[0]) > 500 or abs(car.y - car.lane.car_spawn[1]) > 400:
                                    self.decelerate()
                                    return
                    else:
                        self.accelerate()
            if self.rect.colliderect(self.right.get_bound()):
                if not self.turned:
                    self.is_turning = True
                    self._speed = self.speed_2
                    self.lookahead.width = 1
                    self.lookahead.height = 1
                    randomm = random.randint(2000, 9000)
                    self.lookahead.y = self.rect.y + randomm
                    self.turn_time = time.time()
                car_index = self.right.get_bound().collidelist(oppo_cars)
                if car_index != -1:
                    cat = oppo_cars[car_index]
                    if isinstance(cat.lane, LaneStraight) or isinstance(cat.lane, LaneRight):
                        if self.opposite.get_bound().colliderect(cat):
                            self.decelerate()
                            return
        elif isinstance(self.lane, LaneRight):
            if self.rect.colliderect(self.left.get_bound()):
                if not self.turned:
                    self.is_turning = True
                    self.lookahead.width = 1
                    self.lookahead.height = 1
                    randomm = random.randint(2000, 9000)
                    self.lookahead.x = self.rect.x + randomm
                    self._speed = self.speed_2
                    self.turn_time = time.time()
        if self.lookahead.collidelist(car_rects) != -1:
            self.decelerate()
            return
        else:
            self.accelerate()
        return

    def decelerate(self) -> None:
        if self.state == Car.ACCELERATING:
            self.state = Car.DECELERATING
            self.time = time.time()

    def accelerate(self) -> None:
        if self.state == Car.DECELERATING:
            self.state = Car.ACCELERATING
            self.time = time.time()

    def move(self):
        if self.simulator.paused:
            return

        dt = self.simulator.dt
        game_speed = self.simulator.speed
        current_time = time.time()
        t = min(1, (current_time - self.time))

        if self.is_turning:
            self.update_turn()
        orientation = self.snap_orientation(self.orientation)
        radians = math.radians(orientation)
        # Calculate the magnitude of velocity change

        target_velocity_x = self.speed * math.cos(radians)
        target_velocity_y = self.speed * math.sin(radians)

        if self.state == Car.ACCELERATING:
            # Smoothly interpolate towards the target velocity
            self.velocity[0] = lerp(
                self.velocity[0], target_velocity_x, dt, game_speed)
            self.velocity[1] = lerp(
                self.velocity[1], target_velocity_y, dt, game_speed)
        elif self.state == Car.DECELERATING:
            # Apply gradual deceleration
            # Decelerating faster than accelerating
            self.velocity[0] *= max(0, 1 - 5 * dt * game_speed)
            self.velocity[1] *= max(0, 1 - 5 * dt * game_speed)

        # Enforce speed limit
        speed = math.hypot(self.velocity[0], self.velocity[1])
        if speed > self.speed:
            scaling_factor = self.speed / speed
            self.velocity[0] *= scaling_factor
            self.velocity[1] *= scaling_factor

        # Update position based on new velocity
        self.x += self.velocity[0] * dt
        self.y += self.velocity[1] * dt

        self.rect.x = int(self.x)
        self.rect.y = int(self.y)
        self.lookahead.x = self.rect.x + self.offset[0]
        self.lookahead.y = self.rect.y + self.offset[1]

    def update_turn(self):
        # Calculate the current speed of the car
        current_speed = math.hypot(self.velocity[0], self.velocity[1])

        # Only allow the car to turn if it is moving
        if current_speed > 0 and not self.turned:
            game_speed = self.simulator.speed
            dt = self.simulator.dt
            speed_ratio = current_speed / self.speed
            turn_rate = self.turn_rate * speed_ratio * game_speed * dt * 60
            if isinstance(self.lane, LaneLeft):
                potential_orientation = self.orientation - turn_rate
            elif isinstance(self.lane, LaneRight):
                potential_orientation = self.orientation + turn_rate

            # Normalize the potential orientation to stay within 0-360 degrees
            potential_orientation %= 360

            # Check if the new orientation is within 90 degrees from the original orientation
            if abs(potential_orientation - self.ori_orientation) <= 90 or \
                    abs(potential_orientation - self.ori_orientation) >= 270:
                self.orientation = potential_orientation
            else:
                # Adjust the orientation to not exceed 90 degrees from the original orientation
                if isinstance(self.lane, LaneLeft):
                    self.orientation = (self.ori_orientation - 90) % 360
                elif isinstance(self.lane, LaneRight):
                    self.orientation = (self.ori_orientation + 90) % 360

            # Update turn progress, adjusting for the turn speed and direction multiplier
            self.turn_progress += dt * self.turn_speed * speed_ratio * game_speed

            if self.turn_progress >= 1.0:
                self.is_turning = False
                self.turned = True
                # Assuming speed_2 is a property defining some speed level
                self._speed = self.speed_2 * 2
                # Snap to the nearest 90 degrees

    def snap_orientation(self, orientation):
        # Define the degrees of freedom
        degrees = [0, 90, 180, 270, 360]

        # Normalize the orientation first to ensure it's within the 0-360 range
        normalized_orientation = orientation % 360

        # Find the closest multiple of 90
        closest_degree = min(degrees, key=lambda x: abs(
            x - normalized_orientation))

        # Consider floating-point precision issues
        for degree in degrees:
            # Tolerance for floating-point precision
            if abs(normalized_orientation - degree) < 10.0:
                closest_degree = degree
                break

        return closest_degree

    def update(self) -> None:
        self.check()
        self.rect = self.update_position()
        if abs(self.x - self.lane.car_spawn[0]) > 2000 or abs(self.y - self.lane.car_spawn[1]) > 2000:
            self.lane.road.cars.remove(self)
            self.view.increment_car_leaves()
            del self

    def update_position(self) -> pygame.Rect:
        new_size = self.road.view.rect.size
        original_size = self.old_view_rect

        # Calculate scale factors based on the change in window size
        scale_x = new_size[0] / original_size[0]
        scale_y = new_size[1] / original_size[1]

        # Scale the floating-point coordinates
        self.x *= scale_x
        self.y *= scale_y

        # Update the rectangle for rendering using the scaled floating-point values
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)

        # Optionally scale the size of the rectangle if necessary
        # self.rect.width = int(self.rect.width * scale_y)
        # self.rect.height = int(self.rect.height * scale_y)

        # Update the old view rectangle to the new size for future resizes
        self.old_view_rect = new_size

        return self.rect

    def load_sprites(self) -> list[pygame.Surface]:
        fn = f"{self.color}.png"
        sprite_sheet = pygame.image.load(
            os.path.join("Assets", "cars", fn)
        ).convert_alpha()
        sprite_w = 16
        sprite_h = 16
        sprite_num = sprite_sheet.get_width() // sprite_w

        sprites = []

        for i in range(sprite_num):
            sprite = pygame.Surface((sprite_w, sprite_h), pygame.SRCALPHA)
            sprite.blit(sprite_sheet, (0, 0),
                        (i * sprite_w, 0, sprite_w, sprite_h))
            scaled = pygame.transform.scale(
                sprite, (self.size[0] + 10, self.size[1] + 10))
            sprites.append(scaled)

        self.sprites = sprites

    def draw(self) -> None:
        height = 1
        if self.orientation == 90:  # Game's downward
            render_angle = 270
        elif self.orientation == 270:  # Game's upward
            render_angle = 90
        else:
            render_angle = self.orientation
        for i, img in enumerate(self.sprites):
            rotated_img = pygame.transform.rotate(img, render_angle)
            x = self.rect.x
            y = self.rect.y - i * height

            self.simulator.window.blit(rotated_img, (x, y))
        # pygame.draw.rect(self.road.window, Color.GREEN, self.rects)


class State:

    MENU = 0
    PAUSED = 1
    STANDARD = 2
    ADVANCED = 3
    DUEL_VIEW = 4

    class Light:
        RED = 0
        YELLOW = 1
        GREEN = 2
        PRE_GREEN = 3


class TrafficLight:

    def __init__(self, road: Road, state: State.Light = State.Light.RED) -> None:
        self.road = road
        self.state = state
        self.time = 0.0

    def toggle(self) -> None:
        if self.state == State.Light.GREEN:
            self.state = State.Light.YELLOW
            self.time = time.time()
        elif self.state == State.Light.RED:
            self.state = State.Light.PRE_GREEN
            self.time = time.time()

    def update(self) -> None:
        if self.state == State.Light.YELLOW:
            if (time.time() - self.time) * self.road.view.sim.speed > 4:
                self.state = State.Light.RED
        elif self.state == State.Light.PRE_GREEN:
            if (time.time() - self.time) * self.road.view.sim.speed > 4:
                self.state = State.Light.GREEN

    def color(self) -> list[tuple[int, int, int]]:
        if self.state == State.Light.YELLOW:
            return [Color.INACTIVE_RED, Color.YELLOW, Color.INACTIVE_GREEN]
        elif self.state == State.Light.GREEN:
            return [Color.INACTIVE_RED, Color.INACTIVE_YELLOW, Color.GREEN]
        else:
            return [Color.RED, Color.INACTIVE_YELLOW, Color.INACTIVE_GREEN]

    def draw(self) -> None:
        x, y = self.road.get_light_coords()
        colors = self.color()
        pygame.draw.circle(self.road.window, colors[0], (x, y), 10)
        pygame.draw.circle(self.road.window, colors[1], (x, y + 25), 10)
        pygame.draw.circle(self.road.window, colors[2], (x, y + 50), 10)


class Color:
    """Default Colors"""

    WHITE = (230, 230, 230)
    BLACK = (20, 20, 20)
    RED = (200, 0, 0)
    GREEN = (70, 147, 73)
    BLUE = (0, 0, 230)
    YELLOW = (230, 230, 0)
    GRAY = (200, 200, 200)
    PURPLE = (150, 0, 150)
    CYAN = (0, 230, 230)

    MENU_BG = (1, 1, 1)

    GRASS = (60, 150, 60)
    BUTTON = (90, 90, 90)
    BUTTON_HOVER = (150, 150, 150)

    INACTIVE_RED = (100, 0, 0)
    INACTIVE_YELLOW = (100, 100, 0)
    INACTIVE_GREEN = (0, 100, 0)


class Direction:

    UP = 0
    RIGHT = 1
    DOWN = 2
    LEFT = 3


class UIElement:

    TOP_L = 0
    TOP = 1
    TOP_R = 2
    LEFT = 3
    CENTER = 4
    RIGHT = 5
    BOTTOM_L = 6
    BOTTOM = 7
    BOTTOM_R = 8

    BACKGROUND = 0
    MIDDLEGROUND = 1
    FOREGROUND = 2

    def __init__(self,
                 sim: Simulator,
                 view: Optional[View] = None,
                 *,
                 name: str = "",
                 anchor: int = 0,
                 source: int = 0,
                 offset: tuple[int, int] = (0, 0),
                 color: tuple[int, int, int] = Color.WHITE,
                 background_color: tuple[int, int, int] = Color.WHITE,
                 width: int = 20,
                 height: int = 10,
                 layer: int = 0,
                 auto_margin: bool = True,
                 ) -> None:
        self.sim = sim
        if view:
            self.view = view
        else:
            self.view = self.sim
        self.name = name
        self.anchor = anchor  # frame anchor
        self.source = source  # element anchor
        self.offset = offset
        self.color = color
        self.background_color = background_color
        self.z = layer
        self.width = width
        self.height = height
        self.margin = auto_margin
        self.hidden = False
        self.margin = 10 if auto_margin else 0
        self.rect = pygame.Rect(0, 0, width, height)
        self.update()
        self.load()

    def load(self) -> None:
        self.sim.add_element(self)

    @property
    def x(self) -> int:
        return self.rect.x

    @x.setter
    def x(self, value: int) -> None:
        self.rect.x = value

    @property
    def y(self) -> int:
        return self.rect.y

    @y.setter
    def y(self, value: int) -> None:
        self.rect.y = value

    def margin(self, value: int) -> None:
        self.margin = value

    def hide(self) -> bool:
        self.hidden = True

    def show(self) -> bool:
        self.hidden = False

    def update(self) -> None:
        v_width, v_height = self.view.width, self.view.height
        x, y = self.offset
        x += self.view.rect.x
        y += self.view.rect.y
        m = self.margin

        # Determine outer anchor positions
        match self.anchor:
            case UIElement.TOP_L:
                outer_x = x + m
                outer_y = y + m
            case UIElement.TOP:
                outer_x = v_width // 2 + x
                outer_y = y + m
            case UIElement.TOP_R:
                outer_x = v_width + x - m
                outer_y = y + m
            case UIElement.LEFT:
                outer_x = x + m
                outer_y = v_height // 2 + y
            case UIElement.CENTER:
                outer_x = v_width // 2 + x
                outer_y = v_height // 2 + y
            case UIElement.RIGHT:
                outer_x = v_width + x - m
                outer_y = v_height // 2 + y
            case UIElement.BOTTOM_L:
                outer_x = x + m
                outer_y = v_height + y - m
            case UIElement.BOTTOM:
                outer_x = v_width // 2 + x
                outer_y = v_height + y - m
            case UIElement.BOTTOM_R:
                outer_x = v_width + x - m
                outer_y = v_height + y - m

        # Determine source adjustments within the element
        match self.source:
            case UIElement.TOP_L:
                self.rect.x = outer_x
                self.rect.y = outer_y
            case UIElement.TOP:
                self.rect.centerx = outer_x
                self.rect.y = outer_y
            case UIElement.TOP_R:
                self.rect.right = outer_x
                self.rect.y = outer_y
            case UIElement.LEFT:
                self.rect.x = outer_x
                self.rect.centery = outer_y
            case UIElement.CENTER:
                self.rect.centerx = outer_x
                self.rect.centery = outer_y
            case UIElement.RIGHT:
                self.rect.right = outer_x
                self.rect.centery = outer_y
            case UIElement.BOTTOM_L:
                self.rect.x = outer_x
                self.rect.bottom = outer_y
            case UIElement.BOTTOM:
                self.rect.centerx = outer_x
                self.rect.bottom = outer_y
            case UIElement.BOTTOM_R:
                self.rect.right = outer_x
                self.rect.bottom = outer_y

    @abstractmethod
    def draw(self) -> None:
        ...


class Text(UIElement):

    def __init__(self,
                 sim: Simulator,
                 view: Optional[View] = None,
                 *,
                 name: str = "",
                 anchor: int = 0,
                 source: int = 0,
                 offset: tuple[int, int] = (0, 0),
                 color: tuple[int, int, int] = Color.WHITE,
                 background_color: tuple[int, int, int] = Color.WHITE,
                 width: int = 20,
                 height: int = 10,
                 layer: int = 0,
                 text: str | Callable[[Simulator], str] = "",
                 auto_margin: bool = True,
                 font: pygame.font.Font,
                 dynamic: bool = False
                 ) -> None:
        self.font = font
        self.text = text
        super().__init__(sim, view,
                         name=name,
                         anchor=anchor,
                         offset=offset,
                         source=source,
                         color=color,
                         background_color=background_color,
                         width=width,
                         height=height,
                         layer=layer,
                         auto_margin=auto_margin
                         )

    def update(self) -> None:
        self.text_to_display = self.text(self.sim) if callable(
            self.text) else self.text

        self.text_surface = self.font.render(
            self.text_to_display, True, self.color)

        self.text_width, self.text_height = self.text_surface.get_size()

        self.rect.width = self.text_width
        self.rect.height = self.text_height

        self.text_x = self.rect.x
        self.text_y = self.rect.y
        super().update()

    def draw(self) -> None:
        if self.sim.needs_refresh:
            self.update()
        self.sim.window.fill(self.background_color, self.rect)
        self.update()
        self.sim.window.blit(self.text_surface, (self.text_x, self.text_y))
        pygame.display.update(self.rect)


class Button(UIElement):

    def __init__(self,
                 sim: Simulator,
                 view: Optional[View] = None,
                 *,
                 name: str = "",
                 anchor: int = 0,
                 source: int = 0,
                 offset: tuple[int, int] = (0, 0),
                 color: tuple[int, int, int] = Color.WHITE,
                 background_color: tuple[int, int, int] = Color.WHITE,
                 width: int = 20,
                 height: int = 10,
                 layer: int = 0,
                 auto_margin: bool = True,
                 font: pygame.font.Font,
                 text: str | Callable[[Simulator], str] = "",
                 action: Callable[[Simulator], None] = lambda: None,
                 button_color: tuple[int, int, int] = Color.BUTTON,
                 hover_color: tuple[int, int, int] = Color.BUTTON_HOVER,
                 border_radius: int = -1,
                 ) -> None:
        self.font = font
        self.text = text
        self.button_color = button_color
        self.hover_color = hover_color
        self.border_radius = border_radius
        self.action = action
        super().__init__(sim, view,
                         name=name,
                         anchor=anchor,
                         offset=offset,
                         source=source,
                         color=color,
                         background_color=background_color,
                         width=width,
                         height=height,
                         layer=layer,
                         auto_margin=auto_margin
                         )

    def load(self) -> None:
        self.sim.add_button(self)

    def handle_event(self, event: pygame.event):
        mouse_pos = event.pos  # Get the position of the mouse when clicked
        if self.rect.collidepoint(mouse_pos):
            self.action(self.sim)  # Execute the button's action

    def draw(self) -> None:
        if self.sim.needs_refresh:
            self.update()
        surface = self.sim.window
        text_to_display = self.text(self.sim) if callable(
            self.text) else self.text

        # Render the text
        text_surface = self.font.render(text_to_display, True, self.color)

        # Calculate text width and height
        text_width, text_height = text_surface.get_size()

        # Calculate position based on anchor and offset
        text_x = self.rect.x + (self.rect.width - text_width) // 2
        text_y = self.rect.y + (self.rect.height - text_height) // 2

        mouse_pos = pygame.mouse.get_pos()
        if self.rect.collidepoint(mouse_pos):
            color = self.hover_color
        else:
            color = self.button_color

        # Draw the button background
        pygame.draw.rect(surface, color, self.rect,
                         border_radius=self.border_radius)

        # Blit the text onto the surface at the calculated position
        surface.blit(text_surface, (text_x, text_y))
