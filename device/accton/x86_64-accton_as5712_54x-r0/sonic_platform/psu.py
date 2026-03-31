import glob

from sonic_platform_base.psu_base import PsuBase
from .helper import APIHelper

PSU_NAME_LIST = ['PSU-1', 'PSU-2']

PSU_MAPPING = {
    0: {
        'status_node': '57-0038',
        'hwmon_node': '57-003c',
    },
    1: {
        'status_node': '58-003b',
        'hwmon_node': '58-003f',
    },
}


class Psu(PsuBase):
    """Platform-specific Psu class"""

    def __init__(self, psu_index=0):
        PsuBase.__init__(self)
        self.index = psu_index
        self._api_helper = APIHelper()

        self.status_path = '/sys/bus/i2c/devices/{}/'.format(
            PSU_MAPPING[self.index]['status_node']
        )
        self.hwmon_path = '/sys/bus/i2c/devices/{}/hwmon/hwmon*/'.format(
            PSU_MAPPING[self.index]['hwmon_node']
        )

    def _read_hwmon(self, file_name):
        file_pattern = '{}{}'.format(self.hwmon_path, file_name)
        for file_path in glob.glob(file_pattern):
            value = self._api_helper.read_txt_file(file_path)
            if value is not None:
                return value
        return None

    def _read_bool(self, file_name):
        value = self._api_helper.read_txt_file(self.status_path + file_name)
        if value is None:
            return False
        return int(value, 10) == 1

    def _scaled_value(self, raw_value, divisor):
        if raw_value is None:
            return 0.0
        try:
            return float(raw_value) / divisor
        except ValueError:
            return 0.0

    def get_voltage(self):
        return self._scaled_value(self._read_hwmon('in2_input'), 1000)

    def get_current(self):
        return self._scaled_value(self._read_hwmon('curr2_input'), 1000)

    def get_power(self):
        raw = self._read_hwmon('power2_input')
        if raw is None:
            return 0.0

        try:
            value = float(raw)
            if value >= 100000:
                return value / 1000000
            return value / 1000
        except ValueError:
            return 0.0

    def get_powergood_status(self):
        return self.get_status()

    def set_status_led(self, color):
        return False

    def get_status_led(self):
        return {
            True: self.STATUS_LED_COLOR_GREEN,
            False: self.STATUS_LED_COLOR_RED,
        }.get(self.get_status(), self.STATUS_LED_COLOR_OFF)

    def get_temperature(self):
        return self._scaled_value(self._read_hwmon('temp1_input'), 1000)

    def get_temperature_high_threshold(self):
        value = self._read_hwmon('temp1_max')
        if value is None:
            return None
        return self._scaled_value(value, 1000)

    def get_voltage_high_threshold(self):
        value = self._read_hwmon('in2_max')
        if value is None:
            return None
        return self._scaled_value(value, 1000)

    def get_voltage_low_threshold(self):
        value = self._read_hwmon('in2_min')
        if value is None:
            return None
        return self._scaled_value(value, 1000)

    def get_name(self):
        return PSU_NAME_LIST[self.index]

    def get_presence(self):
        return self._read_bool('psu_present')

    def get_status(self):
        return self._read_bool('psu_power_good')

    def get_model(self):
        model = self._read_hwmon('model_name')
        return model if model is not None else 'N/A'

    def get_serial(self):
        serial = self._read_hwmon('serial_number')
        return serial if serial is not None else 'N/A'

    def get_position_in_parent(self):
        return self.index + 1

    def is_replaceable(self):
        return True
