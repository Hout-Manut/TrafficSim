from __future__ import annotations


class Smart:

    MAX_TIME = 120.0
    BASE_OFFSET = 30.0

    def __init__(self,
                 sim,
                 max_value: int = MAX_TIME,
                 base_offset: int = BASE_OFFSET,
                 increment_value: float = 1.0,
                 no_traffic_multiplier: float = 5.0,
                 value_per_car: float = 1.0
                 ) -> None:
        self.sim = sim
        self.max_value = max_value
        self.base_offset = base_offset
        self.passive_increment = increment_value
        self.no_traffic_multiplier = no_traffic_multiplier
        self.value_per_car = value_per_car
        self.active_cars = 0
        self.active_value = 0
        self.inactive_value = 0
        self.passive_increase = 0.0

    def update(self):
        if self.sim.paused:
            return
        dt = self.sim.dt
        game_speed = self.sim.speed
        self.inactive_value = 0

        active_cars: int = self.sim.get_active_road_cars(1)
        inactive_cars: int = self.sim.get_inactive_road_cars(1)

        if active_cars == 0:
            inactive_boost = self.no_traffic_multiplier
        else:
            inactive_boost = 1

        # Experiment: Active value will never go down
        if active_cars < self.active_cars:
            active_cars = self.active_cars
        else:
            self.active_cars = active_cars

        active_value = (active_cars * self.value_per_car + self.base_offset)

        if active_value > self.max_value:
            active_value = self.max_value

        self.active_value = active_value

        self.passive_increase += self.passive_increment * inactive_boost * dt * game_speed

        self.inactive_value = inactive_cars * self.value_per_car + self.passive_increase



        if self.inactive_value > active_value:
            self.toggle_light()

    def get_current_value(self) -> str:
        return f"{int(self.inactive_value)}:{int(self.active_value)}"

    def toggle_light(self):
        self.sim.toggle_lights(1)
        self.active_cars = 0
        self.active_value = 0
        self.inactive_value = 0
        self.passive_increase = 0


class Basic:

    def __init__(self,
                 sim,
                 value: float = 120.0,
                 ) -> None:
        self.sim = sim
        self.value = value
        self.current = self.value

    def update(self) -> None:
        if self.sim.paused:
            return
        dt = self.sim.dt
        game_speed = self.sim.speed
        self.current -= 1.0 * dt * game_speed
        if self.current < 0.0:
            self.toggle_light()

    def get_current_value(self) -> str:
        return str(int(self.current))

    def toggle_light(self):
        self.sim.toggle_lights(2)
        self.current = self.value
