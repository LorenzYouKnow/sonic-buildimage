from sonic_platform_base.fan_drawer_base import FanDrawerBase

FANS_PER_FANTRAY = 2


class FanDrawer(FanDrawerBase):
    """Platform-specific FanDrawer class"""

    def __init__(self, fantray_index):
        FanDrawerBase.__init__(self)
        self.fantrayindex = fantray_index
        self.__initialize_fan_drawer()

    def __initialize_fan_drawer(self):
        from sonic_platform.fan import Fan

        for i in range(FANS_PER_FANTRAY):
            self._fan_list.append(Fan(self.fantrayindex, i))

    def get_name(self):
        return 'FanTray{}'.format(self.fantrayindex + 1)

    def get_presence(self):
        return self._fan_list[0].get_presence()

    def get_model(self):
        return self._fan_list[0].get_model()

    def get_serial(self):
        return self._fan_list[0].get_serial()

    def get_status(self):
        for fan in self._fan_list:
            if not fan.get_status():
                return False
        return True

    def get_position_in_parent(self):
        return self.fantrayindex + 1

    def is_replaceable(self):
        return True

    def set_status_led(self, color):
        return False

    def get_status_led(self):
        return {
            True: self.STATUS_LED_COLOR_GREEN,
            False: self.STATUS_LED_COLOR_RED,
        }.get(self.get_status(), self.STATUS_LED_COLOR_RED)
