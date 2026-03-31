import glob

from sonic_platform_base.component_base import ComponentBase
from .helper import APIHelper

SYSFS_PATH = '/sys/bus/i2c/devices/'
BIOS_VERSION_PATH = '/sys/class/dmi/id/bios_version'

CPLD_ADDR_MAPPING = {
    'CPLD1': '0060',
    'CPLD2': '0061',
    'CPLD3': '0062',
}

COMPONENT_LIST = [
    ('CPLD1', 'CPLD 1'),
    ('CPLD2', 'CPLD 2'),
    ('CPLD3', 'CPLD 3'),
    ('BIOS', 'Basic Input/Output System'),
]


class Component(ComponentBase):
    """Platform-specific Component class"""

    DEVICE_TYPE = 'component'

    def __init__(self, component_index=0):
        ComponentBase.__init__(self)
        self._api_helper = APIHelper()
        self.index = component_index
        self.name = self.get_name()

    def __get_bios_version(self):
        try:
            with open(BIOS_VERSION_PATH, 'r') as fd:
                return fd.read().strip()
        except Exception:
            return None

    def __get_cpld_version(self):
        cpld_version = {}

        for cpld_name, cpld_addr in CPLD_ADDR_MAPPING.items():
            cpld_version[cpld_name] = 'None'
            version_glob = '{}*-{}/version'.format(SYSFS_PATH, cpld_addr)
            for version_path in glob.glob(version_glob):
                value = self._api_helper.read_txt_file(version_path)
                if value is None:
                    continue
                try:
                    cpld_version[cpld_name] = str(int(value, 16))
                except ValueError:
                    cpld_version[cpld_name] = value
                break

        return cpld_version

    def get_name(self):
        """
        Retrieves the name of the component
        Returns:
            A string containing the name of the component
        """
        return COMPONENT_LIST[self.index][0]

    def get_description(self):
        """
        Retrieves the description of the component
        Returns:
            A string containing the description of the component
        """
        return COMPONENT_LIST[self.index][1]

    def get_firmware_version(self):
        """
        Retrieves the firmware version of module
        Returns:
            string: The firmware versions of the module
        """
        fw_version = None
        if self.name == 'BIOS':
            fw_version = self.__get_bios_version()
        elif 'CPLD' in self.name:
            cpld_version = self.__get_cpld_version()
            fw_version = cpld_version.get(self.name)

        return fw_version

    def install_firmware(self, image_path):
        """
        Install firmware to module
        Args:
            image_path: A string, path to firmware image
        Returns:
            A boolean, True if install successfully, False if not
        """
        raise NotImplementedError

    def get_presence(self):
        return True

    def get_model(self):
        return 'N/A'

    def get_serial(self):
        return 'N/A'

    def get_status(self):
        return True

    def get_position_in_parent(self):
        return -1

    def is_replaceable(self):
        return False
