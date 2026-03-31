import glob
import os

from sonic_platform_base.thermal_base import ThermalBase

THERMAL_NAME_LIST = ['Temp sensor 1', 'Temp sensor 2', 'Temp sensor 3']
THERMAL_SYSFS_PATH = {
    0: '/sys/bus/i2c/devices/61-0048/hwmon/hwmon*/',
    1: '/sys/bus/i2c/devices/62-0049/hwmon/hwmon*/',
    2: '/sys/bus/i2c/devices/63-004a/hwmon/hwmon*/',
}


class Thermal(ThermalBase):
    """Platform-specific Thermal class"""

    def __init__(self, thermal_index=0):
        self.index = thermal_index
        self.hwmon_path = THERMAL_SYSFS_PATH.get(self.index)
        self.ss_index = 1

    def __read_txt_file(self, file_path):
        for filename in glob.glob(file_path):
            try:
                with open(filename, 'r') as fd:
                    return fd.readline().rstrip()
            except IOError:
                pass
        return None

    def __get_temp(self, temp_file):
        temp_file_path = os.path.join(self.hwmon_path, temp_file)
        raw_temp = self.__read_txt_file(temp_file_path)
        if raw_temp is not None:
            return float(raw_temp) / 1000
        return 0.0

    def __set_threshold(self, file_name, temperature):
        temp_file_path = os.path.join(self.hwmon_path, file_name)
        for filename in glob.glob(temp_file_path):
            try:
                with open(filename, 'w') as fd:
                    fd.write(str(temperature))
                return True
            except IOError:
                return False
        return False

    def get_temperature(self):
        temp_file = 'temp{}_input'.format(self.ss_index)
        return self.__get_temp(temp_file)

    def get_high_threshold(self):
        temp_file = 'temp{}_max'.format(self.ss_index)
        return self.__get_temp(temp_file)

    def set_high_threshold(self, temperature):
        temp_file = 'temp{}_max'.format(self.ss_index)
        return self.__set_threshold(temp_file, int(temperature * 1000))

    def get_name(self):
        return THERMAL_NAME_LIST[self.index]

    def get_presence(self):
        temp_file = 'temp{}_input'.format(self.ss_index)
        temp_file_path = os.path.join(self.hwmon_path, temp_file)
        return self.__read_txt_file(temp_file_path) is not None

    def get_status(self):
        temp_file = 'temp{}_input'.format(self.ss_index)
        temp_file_path = os.path.join(self.hwmon_path, temp_file)
        raw_txt = self.__read_txt_file(temp_file_path)
        if raw_txt is None:
            return False
        return int(raw_txt) != 0

    def get_model(self):
        return 'N/A'

    def get_serial(self):
        return 'N/A'

    def get_position_in_parent(self):
        return self.index + 1

    def is_replaceable(self):
        return False
