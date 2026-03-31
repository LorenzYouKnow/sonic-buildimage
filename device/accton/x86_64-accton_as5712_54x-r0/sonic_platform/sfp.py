import os
import time

from sonic_platform_base.sonic_xcvr.sfp_optoe_base import SfpOptoeBase
from sonic_platform_base.sonic_sfp.sfputilhelper import SfpUtilHelper
from sonic_py_common import device_info
from .helper import APIHelper


SFP_STATUS_INSERTED = '1'
SFP_STATUS_REMOVED = '0'


class As5712SfpUtil:
    """AS5712-specific SFP utility for presence/lpmode/reset/event operations."""

    PORT_START = 1
    PORT_END = 54
    PORTS_IN_BLOCK = 54
    QSFP_PORT_START = 49
    QSFP_PORT_END = 54

    BASE_OOM_PATH = '/sys/bus/i2c/devices/{0}-0050/eeprom'
    BASE_CPLD2_PATH = '/sys/bus/i2c/devices/{0}-0061/'
    BASE_CPLD3_PATH = '/sys/bus/i2c/devices/{0}-0062/'
    I2C_BUS_ORDER = -1

    qsfp_sb_map = [0, 2, 4, 1, 3, 5]

    _port_to_i2c_mapping = {
        1: [1, 2],
        2: [2, 3],
        3: [3, 4],
        4: [4, 5],
        5: [5, 6],
        6: [6, 7],
        7: [7, 8],
        8: [8, 9],
        9: [9, 10],
        10: [10, 11],
        11: [11, 12],
        12: [12, 13],
        13: [13, 14],
        14: [14, 15],
        15: [15, 16],
        16: [16, 17],
        17: [17, 18],
        18: [18, 19],
        19: [19, 20],
        20: [20, 21],
        21: [21, 22],
        22: [22, 23],
        23: [23, 24],
        24: [24, 25],
        25: [25, 26],
        26: [26, 27],
        27: [27, 28],
        28: [28, 29],
        29: [29, 30],
        30: [30, 31],
        31: [31, 32],
        32: [32, 33],
        33: [33, 34],
        34: [34, 35],
        35: [35, 36],
        36: [36, 37],
        37: [37, 38],
        38: [38, 39],
        39: [39, 40],
        40: [40, 41],
        41: [41, 42],
        42: [42, 43],
        43: [43, 44],
        44: [44, 45],
        45: [45, 46],
        46: [46, 47],
        47: [47, 48],
        48: [48, 49],
        49: [49, 50],
        50: [51, 52],
        51: [53, 54],
        52: [50, 51],
        53: [52, 53],
        54: [54, 55],
    }

    def __init__(self):
        self.port_to_eeprom_mapping = {}
        for port in range(self.PORT_START, self.PORT_END + 1):
            self.port_to_eeprom_mapping[port] = self.BASE_OOM_PATH.format(
                self._port_to_i2c_mapping[port][1]
            )

        self.data = {'valid': 0, 'last': 0, 'present': 0}

    def get_eeprom_path(self, port_num):
        return self.port_to_eeprom_mapping.get(port_num)

    def update_i2c_order(self):
        if self.I2C_BUS_ORDER < 0:
            if os.path.exists('/sys/bus/i2c/devices/1-0057/eeprom'):
                self.I2C_BUS_ORDER = 0
            if os.path.exists('/sys/bus/i2c/devices/0-0057/eeprom'):
                self.I2C_BUS_ORDER = 1

        if self.I2C_BUS_ORDER < 0:
            self.I2C_BUS_ORDER = 0
        return self.I2C_BUS_ORDER

    def _read_int_file(self, path):
        try:
            with open(path, 'r') as file_obj:
                return int(file_obj.readline().strip(), 10)
        except (IOError, ValueError):
            return None

    def get_presence(self, port_num):
        if port_num < self.PORT_START or port_num > self.PORT_END:
            return False

        order = self.update_i2c_order()
        if port_num <= 24:
            present_path = self.BASE_CPLD2_PATH.format(order)
        else:
            present_path = self.BASE_CPLD3_PATH.format(order)
        present_path = present_path + 'module_present_' + str(port_num)

        value = self._read_int_file(present_path)
        return value == 1

    def qsfp_sb_remap(self, port_num):
        qsfp_index = port_num - self.QSFP_PORT_START
        qsfp_index = self.qsfp_sb_map[qsfp_index]
        return self.QSFP_PORT_START + qsfp_index

    def get_low_power_mode_cpld(self, port_num):
        if port_num < self.QSFP_PORT_START or port_num > self.QSFP_PORT_END:
            return False

        order = self.update_i2c_order()
        lp_mode_path = self.BASE_CPLD3_PATH.format(order) + 'module_lp_mode_'
        lp_mode_path += str(self.qsfp_sb_remap(port_num))

        value = self._read_int_file(lp_mode_path)
        return value == 1

    def get_low_power_mode(self, port_num):
        if port_num < self.QSFP_PORT_START or port_num > self.QSFP_PORT_END:
            return False

        if not self.get_presence(port_num):
            return self.get_low_power_mode_cpld(port_num)

        eeprom = None
        try:
            eeprom = open(self.port_to_eeprom_mapping[port_num], mode='rb', buffering=0)
            eeprom.seek(93)
            raw = eeprom.read(1)
            if not raw:
                return False
            lpmode = raw[0]

            if not (lpmode & 0x1):
                return self.get_low_power_mode_cpld(port_num)

            return (lpmode & 0x2) == 0x2
        except IOError:
            return False
        finally:
            if eeprom is not None:
                eeprom.close()
                time.sleep(0.01)

    def set_low_power_mode(self, port_num, lpmode):
        if port_num < self.QSFP_PORT_START or port_num > self.QSFP_PORT_END:
            return False

        if not self.get_presence(port_num):
            return False

        eeprom = None
        try:
            regval = 0x3 if lpmode else 0x1
            eeprom = open(self.port_to_eeprom_mapping[port_num], mode='r+b', buffering=0)
            eeprom.seek(93)
            eeprom.write(bytes([regval]))
            return True
        except IOError:
            return False
        finally:
            if eeprom is not None:
                eeprom.close()
                time.sleep(0.01)

    def reset(self, port_num):
        if port_num < self.QSFP_PORT_START or port_num > self.QSFP_PORT_END:
            return False

        order = self.update_i2c_order()
        mod_rst_path = self.BASE_CPLD3_PATH.format(order) + 'module_reset_'
        mod_rst_path += str(self.qsfp_sb_remap(port_num))

        try:
            with open(mod_rst_path, 'r+') as reg_file:
                reg_file.seek(0)
                reg_file.write('0')
                reg_file.flush()
                time.sleep(1)
                reg_file.seek(0)
                reg_file.write('1')
                reg_file.flush()
            return True
        except IOError:
            return False

    def _get_presence_bitmap(self):
        order = self.update_i2c_order()
        nodes = [
            self.BASE_CPLD2_PATH.format(order) + 'module_present_all',
            self.BASE_CPLD3_PATH.format(order) + 'module_present_all',
        ]

        bitmap_parts = []
        for node in nodes:
            try:
                with open(node, 'r') as reg_file:
                    bitmap_parts.append(reg_file.readline().strip())
            except IOError:
                return self.data['present']

        rev = ''.join(bitmap_parts[::-1])
        try:
            return int(rev, 16)
        except ValueError:
            return self.data['present']

    def get_transceiver_change_event(self, timeout=2000):
        now = time.time()

        if timeout < 1000:
            timeout = 1000
        timeout = timeout / float(1000)

        if now < (self.data['last'] + timeout) and self.data['valid']:
            return True, {}

        reg_value = self._get_presence_bitmap()
        changed_ports = self.data['present'] ^ reg_value
        if not changed_ports:
            return True, {}

        port_dict = {}
        for port in range(self.PORT_START, self.PORT_END + 1):
            fp_port = self._port_to_i2c_mapping[port][0]
            mask = 1 << (fp_port - 1)
            if changed_ports & mask:
                port_dict[port] = (
                    SFP_STATUS_INSERTED if (reg_value & mask) else SFP_STATUS_REMOVED
                )

        self.data['present'] = reg_value
        self.data['last'] = now
        self.data['valid'] = 1

        return True, port_dict


_SFP_HELPER = As5712SfpUtil()


def get_sfp_util():
    return _SFP_HELPER


class Sfp(SfpOptoeBase):
    """Platform-specific Sfp class"""

    PORT_START = 1
    PORT_END = 54
    QSFP_PORT_START = 49
    QSFP_PORT_END = 54

    _port_name_mapping = None

    def __init__(self, sfp_index=1, sfp_name=None):
        SfpOptoeBase.__init__(self)
        self._api_helper = APIHelper()
        self._sfp_helper = get_sfp_util()

        self.index = sfp_index
        self.port_num = self.index
        self._name = sfp_name
        self.eeprom_path = self._sfp_helper.get_eeprom_path(self.port_num)

        self.refresh()

    @classmethod
    def _load_logical_port_mapping(cls):
        if cls._port_name_mapping is not None:
            return

        try:
            sfputil_helper = SfpUtilHelper()
            port_config_file_path = device_info.get_path_to_port_config_file()
            sfputil_helper.read_porttab_mappings(port_config_file_path)
            cls._port_name_mapping = sfputil_helper.logical
        except Exception:
            cls._port_name_mapping = {}

    def get_eeprom_path(self):
        return self.eeprom_path

    def reset(self):
        if self.port_num < self.QSFP_PORT_START:
            return False
        return self._sfp_helper.reset(self.port_num)

    def get_reset_status(self):
        return False

    def get_name(self):
        if self._name:
            return self._name

        self._load_logical_port_mapping()

        name = None
        if isinstance(self._port_name_mapping, dict):
            name = self._port_name_mapping.get(self.port_num - 1)
        elif isinstance(self._port_name_mapping, list):
            if 0 <= self.port_num - 1 < len(self._port_name_mapping):
                name = self._port_name_mapping[self.port_num - 1]

        if not name:
            name = 'Ethernet{}'.format((self.port_num - 1) * 4)

        return name

    def get_presence(self):
        return self._sfp_helper.get_presence(self.port_num)

    def get_status(self):
        return self.get_presence()

    def refresh(self):
        if self.eeprom_path is None:
            return False

        if not self.get_presence():
            return True

        try:
            self.refresh_xcvr_api()
            return True
        except Exception:
            return False

    def get_lpmode(self):
        if self.port_num < self.QSFP_PORT_START:
            return False
        return self._sfp_helper.get_low_power_mode(self.port_num)

    def set_lpmode(self, lpmode):
        if self.port_num < self.QSFP_PORT_START:
            return False
        return self._sfp_helper.set_low_power_mode(self.port_num, lpmode)

    def get_power_override(self):
        if self.port_num < self.QSFP_PORT_START:
            return False

        try:
            return super(Sfp, self).get_power_override()
        except NotImplementedError:
            return False

    def get_position_in_parent(self):
        return self.port_num

    def is_replaceable(self):
        return True

    def update_sfp_type(self):
        pass

    def get_error_description(self):
        if not self.get_presence():
            return self.SFP_STATUS_UNPLUGGED

        api = self.get_xcvr_api()
        if api is not None:
            try:
                return api.get_error_description()
            except NotImplementedError:
                pass

        return self.SFP_STATUS_OK
