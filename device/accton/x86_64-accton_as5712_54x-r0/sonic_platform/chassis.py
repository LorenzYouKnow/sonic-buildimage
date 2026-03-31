import sys
import subprocess

from sonic_platform_base.chassis_base import ChassisBase
from .helper import APIHelper

NUM_FAN_TRAY = 5
NUM_PSU = 2
NUM_THERMAL = 3
PORT_START = 1
PORT_END = 54
NUM_COMPONENT = 4

HOST_REBOOT_CAUSE_PATH = '/host/reboot-cause/'
PMON_REBOOT_CAUSE_PATH = '/usr/share/sonic/platform/api_files/reboot-cause/'
REBOOT_CAUSE_FILE = 'reboot-cause.txt'
PREV_REBOOT_CAUSE_FILE = 'previous-reboot-cause.txt'
HOST_CHK_CMD = ['docker']

SYSLED_FNODE = '/sys/class/leds/accton_as5712_54x_led::diag/brightness'
SYSLED_MODES = {
    '0': 'STATUS_LED_COLOR_OFF',
    '1': 'STATUS_LED_COLOR_GREEN',
    '2': 'STATUS_LED_COLOR_GREEN_BLINK',
    '3': 'STATUS_LED_COLOR_AMBER',
}


class Chassis(ChassisBase):
    """Platform-specific Chassis class"""

    def __init__(self):
        ChassisBase.__init__(self)
        self._api_helper = APIHelper()
        self.is_host = self._api_helper.is_host()

        self.config_data = {}
        self._eeprom = None
        self.sfp_module_initialized = False

        self.__initialize_fan()
        self.__initialize_psu()
        self.__initialize_thermals()
        self.__initialize_components()
        try:
            self.__initialize_sfp()
        except Exception:
            self.sfp_module_initialized = False

        try:
            self.__initialize_eeprom()
        except Exception:
            self._eeprom = None

    def __initialize_sfp(self):
        from sonic_platform.sfp import Sfp, get_sfp_util

        if self.sfp_module_initialized:
            return

        self._sfp_list = []
        for index in range(PORT_START, PORT_END + 1):
            self._sfp_list.append(Sfp(index))

        self._sfp_helper = get_sfp_util()
        self.sfp_module_initialized = True

    def __initialize_fan(self):
        from sonic_platform.fan_drawer import FanDrawer

        for fan_index in range(NUM_FAN_TRAY):
            fan_drawer = FanDrawer(fan_index)
            self._fan_drawer_list.append(fan_drawer)
            self._fan_list.extend(fan_drawer._fan_list)

    def __initialize_psu(self):
        from sonic_platform.psu import Psu

        for index in range(NUM_PSU):
            self._psu_list.append(Psu(index))

    def __initialize_thermals(self):
        from sonic_platform.thermal import Thermal

        for index in range(NUM_THERMAL):
            self._thermal_list.append(Thermal(index))

    def __initialize_eeprom(self):
        from sonic_platform.eeprom import Tlv

        self._eeprom = Tlv()

    def __ensure_eeprom(self):
        if self._eeprom is None:
            try:
                self.__initialize_eeprom()
            except Exception:
                self._eeprom = None

    def __initialize_components(self):
        from sonic_platform.component import Component

        for index in range(NUM_COMPONENT):
            self._component_list.append(Component(index))

    def __initialize_watchdog(self):
        try:
            from sonic_platform.watchdog import Watchdog

            self._watchdog = Watchdog()
        except Exception:
            self._watchdog = None

    def __is_host(self):
        return subprocess.call(HOST_CHK_CMD) == 0

    def get_name(self):
        self.__ensure_eeprom()
        if self._eeprom is None:
            return self._api_helper.hwsku

        name = self._eeprom.get_product_name()
        if name == 'N/A':
            return self._api_helper.hwsku
        return name

    def get_presence(self):
        return True

    def get_status(self):
        return True

    def get_base_mac(self):
        self.__ensure_eeprom()
        if self._eeprom is None:
            return 'N/A'
        return self._eeprom.get_mac()

    def get_model(self):
        self.__ensure_eeprom()
        if self._eeprom is None:
            return 'N/A'
        return self._eeprom.get_pn()

    def get_serial(self):
        self.__ensure_eeprom()
        if self._eeprom is None:
            return 'N/A'
        return self._eeprom.get_serial()

    def get_system_eeprom_info(self):
        self.__ensure_eeprom()
        if self._eeprom is None:
            return {}
        return self._eeprom.get_eeprom()

    def get_reboot_cause(self):
        reboot_cause_path = HOST_REBOOT_CAUSE_PATH + REBOOT_CAUSE_FILE
        if not self.__is_host():
            reboot_cause_path = PMON_REBOOT_CAUSE_PATH + REBOOT_CAUSE_FILE

        sw_reboot_cause = self._api_helper.read_txt_file(reboot_cause_path) or 'Unknown'

        if sw_reboot_cause != 'Unknown':
            return (self.REBOOT_CAUSE_NON_HARDWARE, sw_reboot_cause)
        return (self.REBOOT_CAUSE_HARDWARE_OTHER, 'Unknown reason')

    def get_change_event(self, timeout=0):
        if not self.sfp_module_initialized:
            self.__initialize_sfp()

        status, changes = self._sfp_helper.get_transceiver_change_event(timeout)
        if not status:
            return False, {'sfp': {}}

        return True, {'sfp': changes}

    def get_sfp(self, index):
        sfp = None
        if not self.sfp_module_initialized:
            self.__initialize_sfp()

        try:
            sfp = self._sfp_list[index - 1]
        except IndexError:
            sys.stderr.write(
                'SFP index {} out of range (1-{})\n'.format(index, len(self._sfp_list))
            )
        return sfp

    def get_position_in_parent(self):
        return -1

    def is_replaceable(self):
        return False

    def initizalize_system_led(self):
        return True

    def get_status_led(self):
        val = self._api_helper.read_txt_file(SYSLED_FNODE)
        return SYSLED_MODES[val] if val in SYSLED_MODES else 'UNKNOWN'

    def set_status_led(self, color):
        mode = None
        for key, value in SYSLED_MODES.items():
            if value == color:
                mode = key
                break

        if mode is None:
            return False

        return self._api_helper.write_txt_file(SYSLED_FNODE, mode)
