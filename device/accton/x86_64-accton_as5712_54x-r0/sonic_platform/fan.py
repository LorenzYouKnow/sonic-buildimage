import os

from sonic_platform_base.fan_base import FanBase
from .helper import APIHelper

SPEED_TOLERANCE = 15
FAN_SYSFS_ROOT = '/sys/devices/platform/as5712_54x_fan'

FAN_NAME_LIST = [
    'FAN-1F',
    'FAN-1R',
    'FAN-2F',
    'FAN-2R',
    'FAN-3F',
    'FAN-3R',
    'FAN-4F',
    'FAN-4R',
    'FAN-5F',
    'FAN-5R',
]


class Fan(FanBase):
    """Platform-specific Fan class"""

    def __init__(self, fan_tray_index, fan_index=0):
        FanBase.__init__(self)
        self._api_helper = APIHelper()
        self.fan_tray_index = fan_tray_index
        self.fan_index = fan_index

    def _front_or_rear_prefix(self):
        return 'fan{}{}'.format('r' if self.fan_index else '', self.fan_tray_index + 1)

    def _get_node_path(self, suffix):
        node = '{}_{}'.format(self._front_or_rear_prefix(), suffix)
        return os.path.join(FAN_SYSFS_ROOT, node)

    def get_direction(self):
        """
        Retrieves the direction of fan
        Returns:
            A string, either FAN_DIRECTION_INTAKE or FAN_DIRECTION_EXHAUST
            depending on fan direction
        """
        direction_path = os.path.join(
            FAN_SYSFS_ROOT, 'fan{}_direction'.format(self.fan_tray_index + 1)
        )
        value = self._api_helper.read_txt_file(direction_path)
        if value is None:
            return self.FAN_DIRECTION_EXHAUST

        return self.FAN_DIRECTION_INTAKE if int(value, 10) == 1 else self.FAN_DIRECTION_EXHAUST

    def get_speed(self):
        """
        Retrieves the speed of fan as a percentage of full speed
        Returns:
            An integer, the percentage of full fan speed, in the range 0 (off)
                 to 100 (full speed)
        """
        if not self.get_presence():
            return 0

        duty_path = os.path.join(
            FAN_SYSFS_ROOT, 'fan{}_duty_cycle_percentage'.format(self.fan_tray_index + 1)
        )
        value = self._api_helper.read_txt_file(duty_path)
        if value is None:
            return 0
        return int(value, 10)

    def get_target_speed(self):
        return self.get_speed()

    def get_speed_tolerance(self):
        return SPEED_TOLERANCE

    def set_speed(self, speed):
        """
        Sets the fan speed
        Args:
            speed: An integer, the percentage of full fan speed to set fan to,
                   in the range 0 (off) to 100 (full speed)
        Returns:
            A boolean, True if speed is set successfully, False if not
        """
        speed = max(0, min(100, int(speed)))
        duty_path = os.path.join(
            FAN_SYSFS_ROOT, 'fan{}_duty_cycle_percentage'.format(self.fan_tray_index + 1)
        )
        return self._api_helper.write_txt_file(duty_path, speed)

    def set_status_led(self, color):
        return False

    def get_status_led(self):
        return {
            True: self.STATUS_LED_COLOR_GREEN,
            False: self.STATUS_LED_COLOR_RED,
        }.get(self.get_status(), self.STATUS_LED_COLOR_RED)

    def get_name(self):
        return FAN_NAME_LIST[self.fan_tray_index * 2 + self.fan_index]

    def get_presence(self):
        speed_path = self._get_node_path('speed_rpm')
        return self._api_helper.read_txt_file(speed_path) is not None

    def get_status(self):
        """
        Retrieves the operational status of the device
        Returns:
            A boolean value, True if device is operating properly, False if not
        """
        if not self.get_presence():
            return False

        fault_path = self._get_node_path('fault')
        value = self._api_helper.read_txt_file(fault_path)
        if value is None:
            return False
        return int(value, 10) == 0

    def get_model(self):
        return 'N/A'

    def get_serial(self):
        return 'N/A'

    def get_position_in_parent(self):
        return self.fan_tray_index * 2 + self.fan_index + 1

    def is_replaceable(self):
        return True
