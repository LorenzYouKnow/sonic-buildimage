import os
import re
import sys

if sys.version_info[0] >= 3:
    from io import StringIO
else:
    from cStringIO import StringIO

from sonic_platform_base.sonic_eeprom import eeprom_tlvinfo

CACHE_ROOT = '/var/cache/sonic/decode-syseeprom'
CACHE_FILE = 'syseeprom_cache'
NULL = 'N/A'


class Tlv(eeprom_tlvinfo.TlvInfoDecoder):
    EEPROM_DECODE_HEADLINES = 6

    def __init__(self):
        self._eeprom_path = '/sys/bus/i2c/devices/1-0057/eeprom'
        if not os.path.exists(self._eeprom_path):
            self._eeprom_path = '/sys/bus/i2c/devices/0-0057/eeprom'
        super(Tlv, self).__init__(self._eeprom_path, 0, '', True)
        self._eeprom = self._load_eeprom()

    def __parse_output(self, decode_output):
        decode_output.replace('\0', '')
        lines = decode_output.split('\n')
        lines = lines[self.EEPROM_DECODE_HEADLINES:]
        eeprom_info = {}

        for line in lines:
            try:
                match = re.search('(0x[0-9a-fA-F]{2})([\\s]+[\\S]+[\\s]+)([\\S]+)', line)
                if match is not None:
                    idx = match.group(1)
                    value = match.group(3).rstrip('\0')
                    eeprom_info[idx] = value
            except Exception:
                pass

        return eeprom_info

    def _load_eeprom(self):
        original_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            self.read_eeprom_db()
        except Exception:
            decode_output = sys.stdout.getvalue()
            sys.stdout = original_stdout
            return self.__parse_output(decode_output)

        status = self.check_status()
        if 'ok' not in status:
            return False

        if not os.path.exists(CACHE_ROOT):
            try:
                os.makedirs(CACHE_ROOT)
            except Exception:
                pass

        try:
            self.set_cache_name(os.path.join(CACHE_ROOT, CACHE_FILE))
        except Exception:
            pass

        eeprom = self.read_eeprom()
        if eeprom is None:
            return {}

        try:
            self.update_cache(eeprom)
        except Exception:
            pass

        self.decode_eeprom(eeprom)
        decode_output = sys.stdout.getvalue()
        sys.stdout = original_stdout

        is_valid, _ = self.is_checksum_valid(eeprom)
        if not is_valid:
            return False

        return self.__parse_output(decode_output)

    def _valid_tlv(self, eeprom_data):
        tlvinfo_type_codes_list = [
            self._TLV_CODE_PRODUCT_NAME,
            self._TLV_CODE_PART_NUMBER,
            self._TLV_CODE_SERIAL_NUMBER,
            self._TLV_CODE_MAC_BASE,
            self._TLV_CODE_MANUF_DATE,
            self._TLV_CODE_DEVICE_VERSION,
            self._TLV_CODE_LABEL_REVISION,
            self._TLV_CODE_PLATFORM_NAME,
            self._TLV_CODE_ONIE_VERSION,
            self._TLV_CODE_MAC_SIZE,
            self._TLV_CODE_MANUF_NAME,
            self._TLV_CODE_MANUF_COUNTRY,
            self._TLV_CODE_VENDOR_NAME,
            self._TLV_CODE_DIAG_VERSION,
            self._TLV_CODE_SERVICE_TAG,
            self._TLV_CODE_VENDOR_EXT,
            self._TLV_CODE_CRC_32,
        ]

        for code in tlvinfo_type_codes_list:
            code_str = '0x{:X}'.format(code)
            eeprom_data[code_str] = eeprom_data.get(code_str, NULL)
        return eeprom_data

    def get_eeprom(self):
        if not isinstance(self._eeprom, dict):
            return {}
        return self._valid_tlv(self._eeprom)

    def get_pn(self):
        if not isinstance(self._eeprom, dict):
            return NULL
        return self._eeprom.get('0x22', NULL)

    def get_serial(self):
        if not isinstance(self._eeprom, dict):
            return NULL
        return self._eeprom.get('0x23', NULL)

    def get_mac(self):
        if not isinstance(self._eeprom, dict):
            return NULL
        return self._eeprom.get('0x24', NULL)

    def get_product_name(self):
        if not isinstance(self._eeprom, dict):
            return NULL
        return self._eeprom.get('0x21', NULL)
