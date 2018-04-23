import ipaddress
import os
import socket
import sys

import udpPacket
import udpWindow


def get_connection_info_and_connect():
    while True:
        this_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        port_number = input("Enter a port number: ")

        if not str(port_number).isdigit():
            print("Invalid port number. Must be a number.")
            continue
        try:
            print("Starting server at port: " + port_number)
            this_socket.bind(('', int(port_number)))
            return this_socket
        except IOError as ioe:
            if ioe.errno == 13:
                print("You do not have permission to use that port number")
                continue
            else:
                print("The following error was found: " + str(ioe))
                continue
        except ValueError as ve:
            print(
                "There was an issue with the entered port number: " + str(ve))
            continue
        except:
            print("Invalid port number")


if __name__ == '__main__':
    my_socket = get_connection_info_and_connect()
    my_socket.setblocking(0)

    while True:
        stay_connected_and_try_again = True
        while stay_connected_and_try_again:
            try:
                received_data, received_address = my_socket.recvfrom(1024)
                packet = udpPacket.Packet(full_packet=received_data)
            except socket.error:
                continue

            try:
                received_data = packet.data.decode("UTF-8")
                # received_data = received_data.decode("utf-8")
            except UnicodeDecodeError:
                received_data = packet.data
                continue

            if received_data:
                if "ket" in received_data or "Received" in received_data:
                    continue
                print("Client has requested the following file: "
                      + received_data)

                if not os.path.isfile(received_data):
                    if packet.check_for_corruption():
                        print("corrupt request.")
                        my_socket.sendto("corrupt".encode("utf-8"),
                                         received_address)
                    else:
                        print(received_data
                              + " was not found. \nAlerting client."
                                " \nWaiting for new request")
                        failure_notice = received_data + " does not exist."
                        my_socket.sendto(failure_notice.encode("utf-8"),
                                         received_address)
                else:
                    stay_connected_and_try_again = False

        packet_size = 1012
        file_size = os.path.getsize(received_data)
        number_of_packets = file_size / packet_size
        number_of_packets_left_over = file_size % packet_size
        current_packet = 0
        window = udpWindow.Window([])

        file = open(received_data, 'rb')
        outgoing_data = file.read(packet_size)
        while outgoing_data:
            number = current_packet

            packet_to_send = udpPacket.Packet(number, outgoing_data)
            full_packet = packet_to_send.get_full_packet()
            encoded_packet = packet_to_send.get_encoded_packet()

            while window.length > 5:
                window.update(my_socket)
            if window.length == 5:
                for packet_from_window in window.contents:
                    if not packet_from_window:
                        continue
                    print("Sending packet " + str(packet_from_window.number))

                    my_socket.sendto(packet_from_window.get_encoded_packet(),
                                     received_address)
                    window.update(my_socket)
            if window.length < 5:
                window.add_packet(packet_to_send)
                print("Sending packet " + str(packet_to_send.number))
                my_socket.sendto(encoded_packet, received_address)

                window.update(my_socket)
                outgoing_data = file.read(packet_size)
                current_packet += 1

        while window.length > 0:
            for packet_from_window in window.contents:
                if not packet_from_window:
                    continue
                print("Sending packet " + str(packet_from_window.number))

                my_socket.sendto(packet_from_window.get_encoded_packet(),
                                 received_address)
                window.update(my_socket)

        file.close()
        print("File was sent!")
        print("Sending transfer confirmation")
        my_socket.sendto("complete".encode("UTF-8"), received_address)

