from __future__ import annotations

import os
import random
import time
from abc import abstractmethod
from typing import Callable, Optional

import pygame

from .utills import ease


class Simulator:

    class View:

        def __init__(self, sim, mode: int) -> None:
            self._sim = sim
            self.mode = mode

            self.road_top = RoadTop(self)
            self.road_right = RoadRight(self)
            self.road_bottom = RoadBottom(self)
            self.road_left = RoadLeft(self)

        @property
        def sim(self) -> Simulator:
            return self._sim

        def get_view(self) -> tuple[int, int, int, int]:
            if self.mode == 0:
                return 0, 0, self.sim.width, self.sim.height
            elif self.mode == 1:
                return 0, 0, self.sim.width // 2, self.sim.height
            else:
                return self.sim.width // 2, 0, self.sim.width // 2, self.sim.height

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

        def draw(self) -> None:
            # if not self._sim.needs_refresh:
            #     return
            # return
            self.road_top.draw()
            self.road_right.draw()
            self.road_bottom.draw()
            self.road_left.draw()

        def __getitem__(self, index) -> Road:
            if index == 0:
                return self.road_top
            if index == 1:
                return self.road_right
            if index == 2:
                return self.road_bottom
            if index == 3:
                return self.road_left
            raise IndexError

    def __init__(self, window: pygame.Surface, device_info: pygame.display.Info, is_fullscreen: bool, flags) -> None:
        self._window = window
        self._last_resolution = (
            self._window.get_width(), self._window.get_height())
        self._device_info = device_info
        self._is_fullscreen = is_fullscreen
        self._running = True
        self.time_started = time.time()
        self.dividers = 2  # Not Implemented: Road Dividers
        self.menu = Menu(self)
        self.bg = Background(self)
        self._state = State.MENU
        self.needs_refresh = True
        self.flags = flags
        self.time_speed = 1
        self.buttons: list[Button] = []

    def update(self) -> None:
        if self.view_1:
            self.view_1.update()
        if self.view_2:
            self.view_2.update()

    def move(self) -> None:
        if self.view_1:
            self.view_1.move()
        if self.view_2:
            self.view_2.move()

    def start(self) -> None:
        self._state = State.DUEL_VIEW

        # self.view_1 = self.View(self, 0)

        self.view_1 = self.View(self, 1)
        self.view_2 = self.View(self, 2)

    @property
    def window(self) -> pygame.Surface:
        return self._window

    @property
    def width(self) -> int:
        return self.window.get_width()

    @property
    def height(self) -> int:
        return self.window.get_height()

    @property
    def state(self) -> State:
        return self._state

    @state.setter
    def state(self, state: State) -> None:
        self._state = state

    @property
    def running(self) -> bool:
        return self._running

    @running.setter
    def running(self, running: bool) -> None:
        self._running = running

    def get_all_cars(self) -> list[Car]:
        return self.road_top._cars + self.road_right._cars + self.road_bottom._cars + self.road_left._cars

    def toggle_fullscreen(self) -> None:
        if self._is_fullscreen:
            self._is_fullscreen = False
            pygame.display.toggle_fullscreen()
            pygame.display.set_mode(self._last_resolution, flags=self.flags)
        else:
            self._is_fullscreen = True
            self._last_resolution = (
                self._window.get_width(),
                self._window.get_height()
            )
            pygame.display.set_mode(
                (self._device_info.current_w,
                 self._device_info.current_h),
                flags=self.flags | pygame.FULLSCREEN
            )
        # pygame.display.toggle_fullscreen()
        self.needs_refresh = True

    def stop(self) -> None:
        self._running = False

    def randomly_add_cars(self, chance: Optional[int] = 50, road_index: Optional[int] = None) -> None:
        roads: list[Road] = []
        if road_index:
            roads.append(self.view_1[road_index])
        else:
            for i in range(4):
                roads.append(self.view_1[i])

        for road in roads:
            if random.randint(0, 100) <= chance:
                direction = random.randint(0, 2)
                road.add_car(direction)

    def draw_boundaries(self) -> None:
        match self.state:
            case State.MENU:
                self.menu.draw()
            case State.STANDARD:
                self.view_1.draw()
            case State.ADVANCED:
                for road in self._roads:
                    road.draw()
            case State.DUEL_VIEW:
                view = 0, 0, self.width // 2, self.height
                mid = view[2] // 2, view[3] // 2

                pygame.draw.circle(self.window, (255, 255, 255), mid, 5)
                view = self.width // 2, 0, self.width // 2, self.height
                mid = view[2] // 2, view[3] // 2

                # draw a dot at the mid point
                pygame.draw.circle(self.window, (255, 255, 255), mid, 5)

                left_rect = pygame.Rect(0, 0, self.width // 2, self.height)
                self.window.set_clip(left_rect)

                self.view_1.draw()

                right_rect = pygame.Rect(
                    self.width // 2, 0, self.width // 2, self.height)
                self.window.set_clip(right_rect)

                self.view_2.draw()

                self.window.set_clip(None)

        self.needs_refresh = False

    def draw(self) -> None:
        ...

    def add_button(self, button: Button) -> None:
        self.buttons.append(button)


class Button:

    def __init__(
        self,
        sim: Simulator,
        name: str,
        coords: tuple[int, int],
        anchor: str = "tl",
        action: Callable[[], None] = lambda: None,
        ) -> None:
        pass

class Menu:

    def __init__(self, sim: Simulator) -> None:
        self._sim = sim
        title_font = pygame.font.Font(
            os.path.join("Assets", "GeosansLight.ttf"), 100)
        self.title = title_font.render("Traffic Simulator", True, Color.BLACK)
        button_font = pygame.font.Font(
            os.path.join("Assets", "Roboto-Light.ttf"), 50)
        self.button_color = Color.BUTTON
        self.button_hover_color = Color.BUTTON_HOVER
        self.buttons: list[tuple[str, pygame.Surface]] = [
            ("Start", button_font.render("Start", True, Color.WHITE)),
            ("Options", button_font.render("Options", True, Color.WHITE)),
            ("Quit", button_font.render("Quit", True, Color.WHITE))
        ]

    @property
    def window(self) -> pygame.Surface:
        return self._sim.window

    def get_title_rect(self) -> pygame.Rect:
        if self._sim.needs_refresh:
            self.title_rect = (
                self.window.get_width() - self.title.get_width() // 2,
                self.window.get_height() // 6
                )
        return self.title_rect

    def get_buttons_rects(self) -> list[pygame.Rect]:
        if self._sim.needs_refresh:
            self.button_rects = []
            for i, (_, button_surf) in enumerate(self.buttons):
                button_rect = button_surf.get_rect(
                    center=(self.window.get_width() // 2,
                            self.window.get_height() // 2 + i * 100))
                self.button_rects.append(button_rect)
        return self.button_rects

    def draw(self) -> None:
        mouse_pos = pygame.mouse.get_pos()
        blit_lists = []
        for rect, (text, button_surf) in zip(self.get_buttons_rects(), self.buttons):
            if rect.collidepoint(mouse_pos):
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
                # Draw hover color
                pygame.draw.rect(self.window, self.button_hover_color, rect)
            else:
                # Draw normal color
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
                pygame.draw.rect(self.window, self.button_color, rect)
            blit_lists.append((button_surf, rect))
        self.window.blits(blit_lists)

        if not self._sim.needs_refresh:
            return
        self._sim.bg.draw()
        self.window.blit(self.title, self.get_title_rect())
        # Draw buttons


class Background:

    def __init__(self, sim: Simulator) -> None:
        self._sim = sim
        self.image = pygame.image.load(os.path.join("Assets", "grass.png"))
        self.width = 80
        self.height = 80
        self.image = pygame.transform.scale(self.image, (self.width, self.height))

    def draw(self) -> None:
        if not self._sim.needs_refresh:
            return
        # return
        self.blit_list = []
        for x in range(0, self._sim.width, self.width):
            for y in range(0, self._sim.height, self.height):
                self.blit_list.append((self.image, (x, y)))
        self._sim.window.blits(self.blit_list)


class Road:

    def __init__(self, view: Simulator.View) -> None:
        self.view = view
        self.get_view = view.get_view
        self.road_width = int(self.window.get_width() * 0.05)
        self._is_active = False
        self._tl = TrafficLight(self)
        self._cars: list[Car] = []
        self._lane_left = LaneLeft(self)
        self._lane_straight = LaneStraight(self)
        self._lane_right = LaneRight(self)
        self._lanes = [self._lane_left, self._lane_straight, self._lane_right]

    @property
    def state(self) -> bool:
        return self._is_active

    @property
    def window(self) -> pygame.Surface:
        return self.view.sim.window

    def switch_state(self) -> None:
        self._is_active = not self._is_active
        if self._is_active:
            self._tl.switch_to_green()
        else:
            self._tl.switch_to_red()

    def add_car(self, direction: int) -> None:
        self._cars.append(Car(self._lanes[direction]))

    def update(self) -> None:
        for car in self._cars:
            car.update()

    def move(self) -> None:
        for car in self._cars:
            car.move()

    @abstractmethod
    def direction(self) -> int:
        ...

    @abstractmethod
    def get_bound(self) -> pygame.Rect:
        ...

    @abstractmethod
    def get_light_bound(self) -> pygame.Rect:
        ...

    def draw(self) -> None:
        pygame.draw.rect(self.window, self.color, self.get_bound(), 2)
        pygame.draw.rect(self.window, self.color, self.get_light_bound(), 5)
        for car in self._cars:
            car.draw()


class RoadTop(Road):

    @property
    def color(self) -> tuple[int, int, int]:
        return Color.PURPLE

    @property
    def direction(self) -> int:
        return 0

    def get_bound(self) -> pygame.Rect:
        view = self.get_view()
        x = view[2] // 2 - self.road_width + view[0]
        y = 0 # + view[1]
        w = self.road_width
        h = view[3]
        return pygame.Rect(x, y, w, h)

    def get_light_bound(self) -> pygame.Rect:
        view = self.get_view()
        x = view[2] // 2 - self.road_width + view[0]
        y = view[3] // 2 - self.road_width
        w = self.road_width
        h = 5
        return pygame.Rect(x, y, w, h)

class RoadRight(Road):

    @property
    def color(self) -> tuple[int, int, int]:
        return Color.RED

    def get_bound(self) -> pygame.Rect:
        view = self.get_view()
        x = 0 + view[0]
        y = view[3] // 2 - self.road_width
        w = view[2]
        h = self.road_width
        return pygame.Rect(x, y, w, h)

    def get_light_bound(self) -> pygame.Rect:
        view = self.get_view()
        x = view[2] // 2 + self.road_width + view[0]
        y = view[3] // 2 - self.road_width
        w = 5
        h = self.road_width
        return pygame.Rect(x, y, w, h)

    @property
    def direction(self) -> int:
        return 1

class RoadBottom(Road):
    @property
    def color(self) -> tuple[int, int, int]:
        return Color.BLUE

    def get_bound(self) -> pygame.Rect:
        view = self.get_view()
        x = (view[2] // 2 ) + view[0]
        y = 0
        w = self.road_width
        h = view[3]
        return pygame.Rect(x, y, w, h)

    def get_light_bound(self) -> pygame.Rect:
        view = self.get_view()
        x = (view[2] // 2) + view[0]
        y = view[3] // 2 + self.road_width
        w = self.road_width
        h = 5
        return pygame.Rect(x, y, w, h)

    @property
    def direction(self) -> int:
        return 2

class RoadLeft(Road):

    @property
    def color(self) -> tuple[int, int, int]:
        return Color.BLACK

    def get_bound(self) -> pygame.Rect:
        view = self.get_view()
        x = 0 + view[0]
        y = view[3] // 2
        w = view[2]
        h = self.road_width
        return pygame.Rect(x, y, w, h)

    def get_light_bound(self) -> pygame.Rect:
        view = self.get_view()
        x = view[2] // 2 - self.road_width + view[0]
        y = view[3] // 2
        w = 5
        h = self.road_width
        return pygame.Rect(x, y, w, h)

    @property
    def direction(self) -> int:
        return 3



class Lane:

    LEFT = 0
    STRAIGHT = 1
    RIGHT = 2

    def __init__(self, road: Road) -> None:
        self._road = road
        view = road.get_view()
        if isinstance(road, RoadTop):
            x = view[2] // 2 - self.road.road_width * 0.8
            y = -100
        elif isinstance(road, RoadRight):
            x = view[2] + 100
            y = view[3] // 2 - self.road.road_width * 0.8
        elif isinstance(road, RoadBottom):
            x = view[2] // 2 + self.road.road_width * 0.6
            y = view[3] + 100
        else:
            x = -100
            y = view[3] // 2 + self.road.road_width * 0.6
        self.car_spawn = (x, y)

    @property
    def window(self) -> pygame.Surface:
        return self._road.window

    @property
    def road(self) -> Road:
        return self._road

    @property
    def width(self) -> int:
        return self._road.road_width // 4

    @abstractmethod
    def direction(self) -> int:
        ...

    @property
    def spawnpoint(self) -> tuple[int, int]:
        return self.car_spawn

class LaneLeft(Lane):

    def __init__(self, road: Road) -> None:
        self._road = road
        view = road.get_view()
        if isinstance(road, RoadTop):
            x = view[2] // 2 - self.road.road_width // 3
            y = -100
        elif isinstance(road, RoadRight):
            x = view[2] + 100
            y = view[3] // 2 - self.road.road_width // 3
        elif isinstance(road, RoadBottom):
            x = view[2] // 2 + self.road.road_width * 0.2
            y = view[3] + 100
        else:
            x = -100
            y = view[3] // 2 + self.road.road_width * 0.2
        self.car_spawn = (x, y)

    @property
    def direction(self) -> int:
        return self.LEFT

class LaneStraight(Lane):

    @property
    def direction(self) -> int:
        return self.STRAIGHT

    @property
    def spawnpoint(self) -> tuple[int, int]:
        return self.car_spawn

class LaneRight(Lane):

    @property
    def direction(self) -> int:
        return self.RIGHT

    @property
    def spawnpoint(self) -> tuple[int, int]:
        return self.car_spawn


class Car:

    SPEED: float = 1
    ACCEL: float = 2

    # STATIONARY = 0
    ACCELERATING = 1
    DECELERATING = 2


    @property
    def position(self) -> tuple[int, int]:
        return self.rect.x, self.rect.y


    def __init__(self,
                 lane: Lane,
                 *,
                 speed: Optional[float] = None,
                 accel: Optional[float] = None) -> None:
        # self._color = random.randint(0, 2)
        self._color = "0"  # Not Implemented: Random Color
        self._lane = lane

        self.width = (lane.width - 1, lane.width - 1)

        r_modifier = random.random()
        self._speed = speed or Car.SPEED + r_modifier * 0.5
        r_modifier = random.random()
        self._accel = accel or Car.ACCEL + r_modifier * 0.5
        x, y = lane.spawnpoint

        # random num from -1 to 1
        ran = [random.uniform(-2, 2), random.uniform(-2, 2)]
        x = x + ran[0]
        y = y + ran[1]

        self.rect = pygame.Rect(x, y, *self.width)

        self.light_bound = self._lane.road.get_light_bound()
        self.state = Car.ACCELERATING
        self.time = time.time()

        self.velocity: list[float] = [0, 0]

        road_dir = lane.road.direction
        if road_dir == 0:
            self.orientaion = 180 # Road from the top, car faces down
            self.left = lane.road.view.road_right
            self.right = lane.road.view.road_left
            self.opposite = lane.road.view.road_bottom
            self.lookahead = pygame.Rect(
                x, y + self.width[0], self.width[0], self.width[1] * 2)
        if road_dir == 1:
            self.orientaion = 270 # Road from the right, car faces left
            self.left = lane.road.view.road_top
            self.right = lane.road.view.road_bottom
            self.opposite = lane.road.view.road_left
            self.lookahead = pygame.Rect(
                x - self.width[0], y, self.width[0] * 2, self.width[1])
        if road_dir == 2:
            self.orientaion = 0 # Road from the bottom, car faces up
            self.left = lane.road.view.road_right
            self.right = lane.road.view.road_left
            self.opposite = lane.road.view.road_top
            self.lookahead = pygame.Rect(
                x, y - self.width[0], self.width[0], self.width[1] * 2)
        if road_dir == 3:
            self.orientaion = 90 # Road from the left, car faces right
            self.left = lane.road.view.road_top
            self.right = lane.road.view.road_bottom
            self.opposite = lane.road.view.road_right
            self.lookahead = pygame.Rect(
                x + self.width[0], y, self.width[0] * 2, self.width[1])

        # self._images: list[pygame.Surface] = []
        # for i in range(16):
        #     image = pygame.image.load(os.path.join(
        #         "Assets", "cars", self._color, str(i) + ".png"))
        #     image = pygame.transform.scale(image, (self.width))
        #     self._images.append(image)

    @property
    def road(self) -> Road:
        return self._lane.road

    @property
    def simulator(self) -> Simulator:
        return self._lane.road._sim

    @property
    def direction(self) -> int:
        return self._lane.direction

    def check(self) -> None:
        car_rects = [car.rect for car in self.road._cars]
        if self.lookahead.colliderect(self.road.get_light_bound()):
            if not self.road._is_active:
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

    def update_velocity(self) -> None:
        t = min(1, time.time() - self.time)
        vol = ease(t)

        if self.state == Car.ACCELERATING:
            velocity_change = vol / 3
        else:
            velocity_change = -vol / 3

        road_dir = self._lane.road.direction
        if road_dir == 0:  # Down
            if self.state == Car.DECELERATING:
                # Only slow down to 0
                self.velocity[1] = max(0, self.velocity[1] + velocity_change)
            else:
                self.velocity[1] = min(
                    self._speed, self.velocity[1] + velocity_change)
        elif road_dir == 1:  # Left
            if self.state == Car.DECELERATING:
                # Only slow down to 0
                self.velocity[0] = min(0, self.velocity[0] - velocity_change)
            else:
                self.velocity[0] = max(-self._speed,
                                       self.velocity[0] - velocity_change)
        elif road_dir == 2:  # Up
            if self.state == Car.DECELERATING:
                # Only slow down to 0
                self.velocity[1] = min(0, self.velocity[1] - velocity_change)
            else:
                self.velocity[1] = max(-self._speed,
                                       self.velocity[1] - velocity_change)
        elif road_dir == 3:  # Right
            if self.state == Car.DECELERATING:
                # Only slow down to 0
                self.velocity[0] = max(0, self.velocity[0] + velocity_change)
            else:
                self.velocity[0] = min(
                    self._speed, self.velocity[0] + velocity_change)

    def move(self) -> None:
        self.rect.x = self.rect.x + self.velocity[0]
        self.rect.y = self.rect.y + self.velocity[1]

        self.lookahead.x  = self.lookahead.x + self.velocity[0]
        self.lookahead.y = self.lookahead.y + self.velocity[1]

    def update(self) -> None:
        self.check()
        self.update_velocity()

    def draw(self) -> None:
        # draw a rect
        pygame.draw.rect(self.road.window, Color.GREEN, self.rect)
        pygame.draw.rect(self.road.window, Color.GRAY, self.lookahead, 2)


class TrafficLight:

    def __init__(self, road: Road) -> None:
        self._road = road
        self._state = State.Light.RED

        size = int(road.window.get_width() * 0.025)
        self._size: tuple[int, int] = (size, size)
        self.base = pygame.Surface(self._size)

    @property
    def window(self) -> pygame.Surface:
        return self._road.window

    @property
    def state(self) -> State.Light:
        return self._state

    @state.setter
    def state(self, state: State.Light) -> None:
        self._state = state

    @property
    def color(self) -> tuple[int, int, int]:
        if self._state == State.Light.RED:
            return Color.RED
        elif self._state == State.Light.YELLOW:
            return Color.YELLOW
        elif self._state == State.Light.GREEN:
            return Color.GREEN

    def switch_to_green(self) -> None:
        self._state = State.Light.GREEN

    def switch_to_red(self) -> None:
        self._state = State.Light.YELLOW
        self._switching = time.time()

    def draw(self) -> None:
        ...


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

    MENU_BG = (1, 1, 1)

    GRASS = (60, 150, 60)
    BUTTON = (100, 100, 100)
    BUTTON_HOVER = (150, 150, 150)


class Direction:

    UP = 0
    RIGHT = 1
    DOWN = 2
    LEFT = 3

    # def __len__(self) -> int:
    #     return 4

    # def __getitem__(self, index) -> int:
    #     return self[index]

    # def __iter__(self):
    #     self.num = 0
    #     return self

    # def __next__(self):
    #     if self.num < len(self):
    #         self.num += 1
    #         return self[self.num - 1]
    #     else:
    #         raise StopIteration


def move(self):
    current_time = time.time()
    dt = self.simulator.dt
    game_speed = self.simulator.speed
    t = min(1, (current_time - self.time) / dt)
    vol = ease(t) * game_speed

    if self.simulator.paused:
        return

    # Scale velocity change by the time speed factor
    vol = self.speed * vol
    if self.state == Car.ACCELERATING:
        velocity_change = (vol) * dt
    else:
        velocity_change = -(vol * 2) * dt

    max_speed = self.speed if self.turn == 0 else self.speed * 0.8

    road_dir = self.lane.road.direction
    if road_dir == 0:  # Down
        self.velocity[1] += velocity_change
        self.velocity[1] = max(0.0, min(max_speed, self.velocity[1])
                                ) if self.state == Car.DECELERATING else min(max_speed, self.velocity[1])
    elif road_dir == 1:  # Left
        self.velocity[0] -= velocity_change
        self.velocity[0] = min(0.0, max(-max_speed, self.velocity[0])
                                ) if self.state == Car.DECELERATING else max(-max_speed, self.velocity[0])
    elif road_dir == 2:  # Up
        self.velocity[1] -= velocity_change
        self.velocity[1] = min(0.0, max(-max_speed, self.velocity[1])
                                ) if self.state == Car.DECELERATING else max(-max_speed, self.velocity[1])
    elif road_dir == 3:  # Right
        self.velocity[0] += velocity_change
        self.velocity[0] = max(0.0, min(max_speed, self.velocity[0])
                                ) if self.state == Car.DECELERATING else min(max_speed, self.velocity[0])

    self.x += self.velocity[0] * dt
    self.y += self.velocity[1] * dt

    self.rect.x = int(self.x)
    self.rect.y = int(self.y)

    self.lookahead.x = self.rect.x + self.offset[0]
    self.lookahead.y = self.rect.y + self.offset[1]
