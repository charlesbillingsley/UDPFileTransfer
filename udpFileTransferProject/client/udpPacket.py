import struct
import zlib


class Packet(object):
    check_value = b''
    number = 0
    data = b''

    def __init__(self, number=None, data=None, full_packet=b''):
        if full_packet:
            self.check_value = full_packet[0:8]
            self.number = int.from_bytes(full_packet[8:12], byteorder='big')
            self.data = full_packet[12:]
        else:
            self.number = number
            self.data = data

    def get_full_packet(self):
        number = self.number.to_bytes(4, byteorder='big')
        data = self.data
        full_packet = number + data
        return full_packet

    def get_encoded_packet(self):
        encoded_data = checksum(self.get_full_packet())
        return encoded_data.to_bytes(8, byteorder='big') + self.get_full_packet()

    def check_for_corruption(self):
        returned_check = checksum(self.get_full_packet())
        if returned_check.to_bytes(8, byteorder='big') == self.check_value:
            return False
        else:
            return True


def checksum(data):
    # value = 0
    # for i in range(0, len(data), 2):
    #     temp_value = data[i]
    #     if (i + 1) < len(data):
    #         temp_value += (data[i + 1] << 8)
    #         value = checksum_adder(value, temp_value)
    # return ~value & 0xffff

    # Couldn't figure out how to calculate it
    # myself reliably so I just used a library
    value = zlib.crc32(data, 0)
    return value & 0xFFFFFFFF


# def checksum_adder(value1, value2):
#     return_value = value1 + value2
#     return (return_value & 0xffff) + return_value
