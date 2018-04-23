import struct
import udpPacket
import time


class Window(object):
    contents = []
    length = 0

    def __init__(self, contents):
        self.contents = contents
        self.length = len(contents)

    def add_packet(self, packet):
        self.contents.append(packet)
        self.length = len(self.contents)

    def get_next_number(self):
        return_value = 0

        for packet in self.contents:
            if not packet:
                continue
            current_number = packet.number + self.length
            return_value = current_number % 10
            break

        return return_value

    def update(self, socket):
        time.sleep(0.001)
        try:
            received_data, received_address = socket.recvfrom(1024)
            if received_data:
                string_data = received_data.decode("UTF-8")
                if "Received packet:" in string_data:
                    for current_data in self.contents:
                        if not current_data:
                            continue

                        received_number = string_data.split(':')
                        print("Received confirmation on packet: "
                              + received_number[1])
                        if current_data.number == int(received_number[1]):
                            self.contents.remove(current_data)
                            self.length -= 1
        except (UnicodeDecodeError, TypeError, IOError, ValueError):
            pass
