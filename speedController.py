import numpy as np
from time import time


class SpeedController:
    def __init__(self):
        self.last_speed_change = time()
        self.current_speed = 300  # Initial default speed (middle of range)
        self.speed_history = []
        # Configuration
        self.MIN_SPEED = 200  # Slowest allowed speed
        self.MAX_SPEED = 550  # Fastest allowed speed
        self.MIN_CHANGE_DELAY = 5  # seconds between speed changes
        self.SMOOTHING_WINDOW = 3  # number of samples for moving average
        self.MAX_COUNT = 20  # Expected maximum object count
        self.MAX_AREA = 500  # Expected maximum area (cm²)
        self.COUNT_WEIGHT = 0.3  # Influence of object count
        self.AREA_WEIGHT = 0.7  # Influence of object area
        self.MAX_STEPS = 4
        self.MIN_STEPS = 0

    def _normalize(self, value, max_value):
        return 1.0 - min(value / max_value, 1.0)  # Inverted normalization

    def _calculate_target_speed(self, object_count, total_area):
        norm_count = self._normalize(object_count, self.MAX_COUNT)
        norm_area = self._normalize(total_area, self.MAX_AREA)

        # Weighted combination of factors
        speed_factor = (self.COUNT_WEIGHT * norm_count) + (self.AREA_WEIGHT * norm_area)

        # Calculate speed (higher factor = higher speed)
        return int(self.MIN_SPEED + speed_factor * (self.MAX_SPEED - self.MIN_SPEED))

    def _apply_smoothing(self, target_speed):
        """Apply moving average smoothing to speed changes"""
        self.speed_history.append(target_speed)
        if len(self.speed_history) > self.SMOOTHING_WINDOW:
            self.speed_history.pop(0)
        return int(np.mean(self.speed_history))

    def _should_update_speed(self, new_speed):
        """Determine if speed should be updated based on timing and significance"""
        time_since_change = time() - self.last_speed_change
        speed_delta = abs(new_speed - self.current_speed)
        min_delta = 0.05 * (self.MAX_SPEED - self.MIN_SPEED)

        return (time_since_change >= self.MIN_CHANGE_DELAY and
                (speed_delta >= min_delta or not self.speed_history))

    def update_speed(self, object_count, total_area):
        """Main interface to calculate and update speed"""
        target_speed = self._calculate_target_speed(object_count, total_area)
        smoothed_speed = self._apply_smoothing(target_speed)

        if self._should_update_speed(smoothed_speed):
            self.current_speed = smoothed_speed
            self.last_speed_change = time()
            return True
        return False

    def lerp_based_on_steps(self, occupied_steps):
        max_speed = 400
        min_speed = 100
        targeted_speed = max_speed - (max_speed - min_speed)*((self.MAX_STEPS - occupied_steps)/(self.MAX_STEPS - self.MIN_STEPS))
        return targeted_speed

    def update_speed_of_motor_two(self, stepStatus):
        numOfStepsOccupied = sum(stepStatus)
        target_speed = self.lerp_based_on_steps(numOfStepsOccupied)
        smoothed_speed = self._apply_smoothing(target_speed)
        if self._should_update_speed(smoothed_speed):
            self.current_speed = smoothed_speed
            self.last_speed_change = time()
            return True
        return False

    def get_current_speed(self):
        """Get the current active speed"""
        return self.current_speed