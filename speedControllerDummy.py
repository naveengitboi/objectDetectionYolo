import numpy as np
from time import time


class DualMotorSpeedController:
    def __init__(self):
        # Motor 1 configuration (object/area based)
        self.motor1 = {
            'last_speed_change': time(),
            'current_speed': 300,
            'speed_history': [],
            'MIN_SPEED': 200,
            'MAX_SPEED': 550,
            'MIN_CHANGE_DELAY': 5,
            'SMOOTHING_WINDOW': 3,
            'MAX_COUNT': 20,
            'MAX_AREA': 500,
            'COUNT_WEIGHT': 0.3,
            'AREA_WEIGHT': 0.7
        }

        # Motor 2 configuration (steps-based)
        self.motor2 = {
            'last_speed_change': time(),
            'current_speed': 300,
            'speed_history': [],
            'MIN_SPEED': 100,
            'MAX_SPEED': 400,
            'MIN_CHANGE_DELAY': 5,
            'SMOOTHING_WINDOW': 3,
            'MAX_STEPS': 4,
            'MIN_STEPS': 0
        }

    def _normalize(self, value, max_value):
        return 1.0 - min(value / max_value, 1.0)

    def _calculate_motor1_speed(self, object_count, total_area):
        norm_count = self._normalize(object_count, self.motor1['MAX_COUNT'])
        norm_area = self._normalize(total_area, self.motor1['MAX_AREA'])
        speed_factor = (self.motor1['COUNT_WEIGHT'] * norm_count) + \
                       (self.motor1['AREA_WEIGHT'] * norm_area)
        return int(self.motor1['MIN_SPEED'] + speed_factor *
                   (self.motor1['MAX_SPEED'] - self.motor1['MIN_SPEED']))

    def _calculate_motor2_speed(self, stepStatus):
        num_steps = sum(stepStatus)
        max_speed = self.motor2['MAX_SPEED']
        min_speed = self.motor2['MIN_SPEED']
        return max_speed - (max_speed - min_speed) * (
                (self.motor2['MAX_STEPS'] - num_steps) /
                (self.motor2['MAX_STEPS'] - self.motor2['MIN_STEPS']))

    def _apply_smoothing(self, motor, target_speed):
        motor['speed_history'].append(target_speed)
        if len(motor['speed_history']) > motor['SMOOTHING_WINDOW']:
            motor['speed_history'].pop(0)
        return int(np.mean(motor['speed_history']))

    def _should_update_speed(self, motor, new_speed):
        time_since_change = time() - motor['last_speed_change']
        speed_delta = abs(new_speed - motor['current_speed'])
        min_delta = 0.05 * (motor['MAX_SPEED'] - motor['MIN_SPEED'])

        return (time_since_change >= motor['MIN_CHANGE_DELAY'] and
                (speed_delta >= min_delta or not motor['speed_history']))

    def update_motor1_speed(self, object_count, total_area):
        target_speed = self._calculate_motor1_speed(object_count, total_area)
        smoothed_speed = self._apply_smoothing(self.motor1, target_speed)

        if self._should_update_speed(self.motor1, smoothed_speed):
            self.motor1['current_speed'] = smoothed_speed
            self.motor1['last_speed_change'] = time()
            return True
        return False

    def update_motor2_speed(self, stepStatus):
        target_speed = self._calculate_motor2_speed(stepStatus)
        smoothed_speed = self._apply_smoothing(self.motor2, target_speed)

        if self._should_update_speed(self.motor2, smoothed_speed):
            self.motor2['current_speed'] = smoothed_speed
            self.motor2['last_speed_change'] = time()
            return True
        return False

    def get_motor1_speed(self):
        return self.motor1['current_speed']

    def get_motor2_speed(self):
        return self.motor2['current_speed']