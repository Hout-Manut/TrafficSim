from __future__ import annotations

import os
import random
import time
from abc import abstractmethod
from typing import Callable, Optional

import numpy as np
import pygame

from .utills import ease, get_mid_coord


class Simulator:

    def __init__(self,
                 window: pygame.Surface,
                 device_info,
                 is_fullscreen,
                 user_event_1,
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

        self.needs_refresh = True
        self.bg_elements: list[UIElement] = []
        self.mg_elements: list[UIElement] = []
        self.fg_elements: list[UIElement] = []
        self.buttons: list[Button] = []
        self.paused = False
        self.dt = 0.0

    @property
    def speed(self) -> float:
        return 0.0 if self.paused else self.time_speed

    @property
    def speed_str(self) -> str:
        return "Paused" if self.paused else f"{self.speed:.2f}x"

    @speed.setter
    def speed(self, value: float) -> None:
        self.time_speed = value

    def increase_speed(self) -> None:
        if self.paused:
            self.pause()
        self.time_speed = min(2.0, self.time_speed + 0.1)
        self.update_events()

    def decrease_speed(self) -> None:
        if self.paused:
            self.pause()
        self.time_speed = max(0.0, self.time_speed - 0.1)
        self.update_events()

    def update_events(self) -> None:
        pygame.time.set_timer(self.randomly_add_cars_event, int(1000 * self.time_speed))

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

    def pause(self) -> None:
        self.paused = not self.paused

    def randomly_add_cars(self, chance: Optional[int] = 50, road_index: Optional[int] = None) -> None:
        ran = random.randint(0, 100)
        if road_index:
            if ran <= chance:
                direction = random.randint(0, 2)
                self.view_1[road_index].add_car(direction)
                self.view_2[road_index].add_car(direction)
        else:
            road_index = random.randint(0, 3)
            if ran <= chance:
                direction = random.randint(0, 2)
                self.view_1[road_index].add_car(direction)
                self.view_2[road_index].add_car(direction)

    def draw_debug(self) -> None:
        self.view_1.draw_debug()
        self.view_2.draw_debug()

    def draw(self) -> None:
        for element in self.bg_elements:
            element.draw()
        self.view_1.draw()
        self.view_2.draw()
        for element in self.mg_elements:
            element.draw()
        for element in self.fg_elements:
            element.draw()
        for button in self.buttons:
            button.draw()

    def update(self) -> None:
        # if self.needs_refresh:
        self.view_1.update()
        self.view_2.update()

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

        self.road_top = RoadTop(self)
        self.road_right = RoadRight(self)
        self.road_bottom = RoadBottom(self)
        self.road_left = RoadLeft(self)

    @property
    def width(self) -> int:
        return self.rect.width

    @property
    def height(self) -> int:
        return self.rect.height

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

    def draw(self) -> None:
        # if not self._sim.needs_refresh:
        #     return
        # return
        self.sim.window.set_clip(self.rect)
        # self.road_top.draw()
        # self.road_right.draw()
        # self.road_bottom.draw()
        # self.road_left.draw()
        self.sim.window.set_clip(None)
        ...

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

    def __init__(self, view: View) -> None:
        self.view = view
        self.light = TrafficLight(self)
        self.lane_left = LaneLeft(self)
        self.lane_straight = LaneStraight(self)
        self.lane_right = LaneRight(self)
        self.lanes = [self.lane_left, self.lane_straight, self.lane_right]
        self.rect = self.get_bound()
        self.light_rect = self.get_light_bound()
        self.cars: list[Car] = []

    @property
    def is_active(self) -> bool:
        return True if self.light.state == State.Light.GREEN else False
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

    def add_car(self, direction: int) -> None:
        self.cars.append(Car(self.lanes[direction]))

    def update(self) -> None:
        if self.view.sim.needs_refresh:
            self.rect = self.get_bound()
            self.light_rect = self.get_light_bound()
        for car in self.cars:
            car.update()

    def move(self) -> None:
        for car in self.cars:
            car.move()

    @abstractmethod
    def get_light_coords(self) -> tuple[int, int]:
        ...

    @abstractmethod
    def direction(self) -> int:
        ...

    @abstractmethod
    def get_bound(self) -> pygame.Rect:
        ...

    @abstractmethod
    def get_light_bound(self) -> pygame.Rect:
        ...

    def draw_debug(self) -> None:
        if self.view.sim.needs_refresh:
            self.rect = self.get_bound()
            self.light_rect = self.get_light_bound()

        pygame.draw.rect(self.window, self.color, self.rect, 2)
        pygame.draw.rect(self.window, self.color, self.light_rect, 5)
        for car in self.cars:
            car.draw()


class RoadTop(Road):

    @property
    def color(self) -> tuple[int, int, int]:
        return Color.PURPLE

    @property
    def direction(self) -> int:
        return 0

    def get_bound(self) -> pygame.Rect:
        view = [self.view.rect.x, self.view.rect.y,
                self.view.rect.width, self.view.rect.height]
        x = view[2] // 2 - self.road_width + view[0]
        y = 0  # + view[1]
        w = self.road_width
        h = view[3]
        return pygame.Rect(x, y, w, h)

    def get_light_bound(self) -> pygame.Rect:
        view = [self.view.rect.x, self.view.rect.y,
                self.view.rect.width, self.view.rect.height]
        x = view[2] // 2 - self.road_width + view[0]
        y = view[3] // 2 - self.road_width
        w = self.road_width
        h = 5
        return pygame.Rect(x, y, w, h)

    def get_light_coords(self) -> tuple[int, int]:
        view = [self.view.rect.x, self.view.rect.y,
                self.view.rect.width, self.view.rect.height]
        x = view[2] // 2 - self.road_width * 2
        y = view[3] // 2 - self.road_width * 2
        return x, y


class RoadRight(Road):

    @property
    def color(self) -> tuple[int, int, int]:
        return Color.RED

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
        x = view[2] // 2 + self.road_width + view[0]
        y = view[3] // 2 - self.road_width
        w = 5
        h = self.road_width
        return pygame.Rect(x, y, w, h)

    def get_light_coords(self) -> tuple[int, int]:
        view = [self.view.rect.x, self.view.rect.y,
                self.view.rect.width, self.view.rect.height]
        x = view[2] // 2 + self.road_width * 2
        y = view[3] // 2 - self.road_width * 2
        return x, y

    @property
    def direction(self) -> int:
        return 1


class RoadBottom(Road):
    @property
    def color(self) -> tuple[int, int, int]:
        return Color.BLUE

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
        y = view[3] // 2 + self.road_width
        w = self.road_width
        h = 5
        return pygame.Rect(x, y, w, h)

    def get_light_coords(self) -> tuple[int, int]:
        view = [self.view.rect.x, self.view.rect.y,
                self.view.rect.width, self.view.rect.height]
        x = view[2] // 2 + self.road_width * 2
        y = view[3] // 2 + self.road_width * 2
        return x, y

    @property
    def direction(self) -> int:
        return 2


class RoadLeft(Road):

    @property
    def color(self) -> tuple[int, int, int]:
        return Color.BLACK

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
        x = view[2] // 2 - self.road_width + view[0]
        y = view[3] // 2
        w = 5
        h = self.road_width
        return pygame.Rect(x, y, w, h)

    def get_light_coords(self) -> tuple[int, int]:
        view = [self.view.rect.x, self.view.rect.y,
                self.view.rect.width, self.view.rect.height]
        x = view[2] // 2 - self.road_width * 2
        y = view[3] // 2 + self.road_width * 2
        return x, y

    @property
    def direction(self) -> int:
        return 3


class Lane:

    def __init__(self, road: Road) -> None:
        self.road = road
        self.view = road.view

    def get_car_spawn(self) -> tuple[int, int]:
        view = [self.view.rect.x, self.view.rect.y,
                self.view.rect.width, self.view.rect.height]
        print(view)
        if isinstance(self.road, RoadTop):
            x = (view[2] // 2 - self.road.road_width * 0.8) + view[0]
            y = -100
        elif isinstance(self.road, RoadRight):
            x = (view[2] + 100) + view[0]
            y = view[3] // 2 - self.road.road_width * 0.8
        elif isinstance(self.road, RoadBottom):
            x = (view[2] // 2 + self.road.road_width * 0.6) + view[0]
            y = view[3] + 100
        else:
            x = -100 + view[0]
            y = view[3] // 2 + self.road.road_width * 0.6
        return (x, y)

    @property
    def car_spawn(self) -> tuple[int, int]:
        return self.get_car_spawn()

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

    def __init__(self,
                 lane: Lane,
                 *,
                 speed: Optional[float] = None,
                 accel: Optional[float] = None
                 ) -> None:
        print(f"[Car.__init__] Creating car in lane {lane.road.direction}")
        self.lane = lane

        self.size = (30, 30)
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

        self.light_bound = self.lane.road.get_light_bound()
        self.state = Car.ACCELERATING
        self.time = time.time()

        self.velocity: list[float] = [0, 0]
        road_dir = lane.road.direction
        ran = random.randint(0, 3)
        ran += 1
        if road_dir == 0:
            print("[Car.__init__] Car on top road")
            self.orientaion = 180  # Road from the top, car faces down
            self.left = lane.road.view.road_right
            self.right = lane.road.view.road_left
            self.opposite = lane.road.view.road_bottom
            self.offset = 0, self.size[0] + ran
            self.lookahead = pygame.Rect(
                x, y + self.offset[1], self.size[0], self.size[1] * 2)
        elif road_dir == 1:
            print("[Car.__init__] Car on right road")
            self.orientaion = 270  # Road from the right, car faces left
            self.left = lane.road.view.road_top
            self.right = lane.road.view.road_bottom
            self.opposite = lane.road.view.road_left
            self.offset = -(self.size[0] * 2 + ran), 0
            self.lookahead = pygame.Rect(
                x + self.offset[0], y, self.size[0] * 2, self.size[1])
        elif road_dir == 2:
            print("[Car.__init__] Car on bottom road")
            self.orientaion = 0  # Road from the bottom, car faces up
            self.left = lane.road.view.road_right
            self.right = lane.road.view.road_left
            self.opposite = lane.road.view.road_top
            self.offset = 0, -(self.size[0] * 2 + ran)
            self.lookahead = pygame.Rect(
                x, y + self.offset[1], self.size[0], self.size[1] * 2)
        else:
            print("[Car.__init__] Car on left road")
            self.orientaion = 90  # Road from the left, car faces right
            self.left = lane.road.view.road_top
            self.right = lane.road.view.road_bottom
            self.opposite = lane.road.view.road_right
            self.offset = self.size[0] + ran, 0
            self.lookahead = pygame.Rect(
                x + self.offset[0], y, self.size[0] * 2, self.size[1])

    @property
    def speed(self) -> float:
        return self._speed * self.simulator.speed

    @property
    def road(self) -> Road:
        return self.lane.road

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
        car_rects = [car.rect for car in self.road.cars if car is not self]
        if self.lookahead.colliderect(self.road.get_light_bound()):
            if not self.road.is_active:
                self.decelerate()
                return
            elif self.opposite.get_bound().collidelist(car_rects) != -1:
                self.decelerate()
                return
            else:
                self.accelerate()
            return
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
        current_time = time.time()
        dt = self.simulator.dt
        game_speed = self.simulator.speed
        if game_speed == 0.0:
            return
        t = min(1, (current_time - self.time) / dt)
        vol = ease(t) * game_speed

        # Scale velocity change by the time speed factor
        vol = self.speed * vol
        if self.state == Car.ACCELERATING:
            velocity_change = (vol) * dt
        else:
            velocity_change = -(vol * 5) * dt

        road_dir = self.lane.road.direction
        if road_dir == 0:  # Down
            self.velocity[1] += velocity_change
            self.velocity[1] = max(0.0, min(self.speed, self.velocity[1])
                                   ) if self.state == Car.DECELERATING else min(self.speed, self.velocity[1])
        elif road_dir == 1:  # Left
            self.velocity[0] -= velocity_change
            self.velocity[0] = min(0.0, max(-self.speed, self.velocity[0])
                                   ) if self.state == Car.DECELERATING else max(-self.speed, self.velocity[0])
        elif road_dir == 2:  # Up
            self.velocity[1] -= velocity_change
            self.velocity[1] = min(0.0, max(-self.speed, self.velocity[1])
                                   ) if self.state == Car.DECELERATING else max(-self.speed, self.velocity[1])
        elif road_dir == 3:  # Right
            self.velocity[0] += velocity_change
            self.velocity[0] = max(0.0, min(self.speed, self.velocity[0])
                                   ) if self.state == Car.DECELERATING else min(self.speed, self.velocity[0])

        self.x += self.velocity[0] * dt
        self.y += self.velocity[1] * dt

        self.rect.x = int(self.x)
        self.rect.y = int(self.y)

        self.lookahead.x = self.rect.x + self.offset[0]
        self.lookahead.y = self.rect.y + self.offset[1]

    def update(self) -> None:
        self.check()
        self.rect = self.update_position()

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
        self.rect.x *= int(self.x)
        self.rect.y *= int(self.y)

        # Optionally scale the size of the rectangle if necessary
        # self.rect.width = int(self.rect.width * scale_y)
        # self.rect.height = int(self.rect.height * scale_y)

        # Update the old view rectangle to the new size for future resizes
        self.old_view_rect = new_size

        return self.rect

    def draw(self) -> None:
        pygame.draw.rect(self.road.window, Color.GREEN, self.rect)
        pygame.draw.rect(self.road.window, Color.GRAY, self.lookahead, 2)


class TrafficLight:

    def __init__(self, road: Road) -> None:
        self.road = road
        self.state = State.Light.RED

    @property
    def coords(self) -> tuple[int, int]:
        return self.road.get_light_coords()

    def color(self) -> tuple[int, int, int]:
        if self.state == State.Light.RED:
            return Color.RED
        elif self.state == State.Light.YELLOW:
            return Color.YELLOW
        elif self.state == State.Light.GREEN:
            return Color.GREEN

    def draw(self) -> None:
        x, y = self.coords
        pygame.draw.rect(self.road.window, self.color(), (x, y, *self.road.light._size))




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


class Color:
    """Default Colors"""

    WHITE = (230, 230, 230)
    BLACK = (20, 20, 20)
    RED = (230, 0, 0)
    GREEN = (0, 230, 0)
    BLUE = (0, 0, 230)
    YELLOW = (230, 230, 0)
    GRAY = (200, 200, 200)
    PURPLE = (150, 0, 150)
    CYAN = (0, 230, 230)

    MENU_BG = (1, 1, 1)

    GRASS = (60, 150, 60)
    BUTTON = (100, 100, 100)
    BUTTON_HOVER = (150, 150, 150)


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
                 offset: tuple[int, int] = (0, 0),
                 color: tuple[int, int, int] = Color.WHITE,
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
        self.anchor = anchor
        self.offset = offset
        self.color = color
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
        m = self.margin

        match self.anchor:
            case UIElement.TOP_L:
                self.rect.x = x + m
                self.rect.y = y + m
            case UIElement.TOP:
                self.rect.centerx = v_width // 2 + x
                self.rect.y = y + m
            case UIElement.TOP_R:
                self.rect.right = v_width + x - m
                self.rect.y = y + m
            case UIElement.LEFT:
                self.rect.x = x + m
                self.rect.centery = v_height // 2 + y
            case UIElement.CENTER:
                self.rect.centerx = v_width // 2 + x
                self.rect.centery = v_height // 2 + y
            case UIElement.RIGHT:
                self.rect.right = v_width + x - m
                self.rect.centery = v_height // 2 + y
            case UIElement.BOTTOM_L:
                self.rect.x = x + m
                self.rect.bottom = v_height + y - m
            case UIElement.BOTTOM:
                self.rect.centerx = v_width // 2 + x
                self.rect.bottom = v_height + y - m
            case UIElement.BOTTOM_R:
                self.rect.right = v_width + x - m
                self.rect.bottom = v_height + y - m

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
                 offset: tuple[int, int] = (0, 0),
                 color: tuple[int, int, int] = Color.WHITE,
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
                         color=color,
                         width=width,
                         height=height,
                         layer=layer,
                         auto_margin=auto_margin
                         )

    def update(self) -> None:
        self.text_to_display = self.text(self.sim) if callable(
            self.text) else self.text

        self.text_surface = self.font.render(self.text_to_display, True, self.color)

        self.text_width, self.text_height = self.text_surface.get_size()

        self.rect.width = self.text_width
        self.rect.height = self.text_height

        self.text_x = self.rect.x
        self.text_y = self.rect.y
        super().update()


    def draw(self) -> None:
        # if not self.sim.needs_refresh:
        #     return
        self.sim.window.fill(Color.WHITE, self.rect)
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
                 offset: tuple[int, int] = (0, 0),
                 color: tuple[int, int, int] = Color.WHITE,
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
                         color=color,
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
        text_to_display = self.text(self.sim) if callable(self.text) else self.text

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
