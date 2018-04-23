import ipaddress
import os
import select
import socket

import udpPacket


def get_connection_info():
    server_address = input("Enter an ip address: ")
    received_valid_address = False
    while not received_valid_address:
        try:
            ipaddress.ip_address(server_address)
            received_valid_address = True
        except ValueError:
            server_address = input("Invalid ip address. Try again: ")
            received_valid_address = False

    received_valid_port_number = False
    port_number = input("Enter a port number: ")
    while not received_valid_port_number:
        if not port_number.isdigit():
            port_number = input("Invalid port number. Try again: ")
        else:
            received_valid_port_number = True

    return server_address, int(port_number)


def get_file_name_from_user():
    requested_file = input(
        "Please enter a file name and extention: ")
    while True:
        if "." not in requested_file:
            requested_file = input(
                "Filename must have extention. Try again: ")
        else:
            return requested_file


# Main Method
if __name__ == '__main__':
    full_address = get_connection_info()
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    my_socket.connect(full_address)

    file_name = get_file_name_from_user()
    my_socket.send(file_name.encode("UTF-8"))

    finished_packets = []
    waiting_packets = []
    number_of_packets_written = 0

    file = open(file_name, 'wb')
    my_socket.setblocking(0)

    while True:
        count = 0
        while True:
            received_data = select.select([my_socket], [], [], 3)

            if received_data[0]:
                current_data = my_socket.recv(1024)
                break
            else:
                if count > 3:
                    print("Request failed too many times. Exiting...")
                    exit(0)
                my_socket.send(file_name.encode("UTF-8"))
                count += 1

        if not current_data:
            break

        try:
            if "complete" in current_data.decode("UTF-8"):
                break
            if "does not exist" in current_data.decode("UTF-8"):
                print("File does not exist on the server.")
                file.close()
                my_socket.close()
                os.remove(file_name)
                print("Exiting")
                exit()
        except (UnicodeDecodeError, TypeError):
            pass

        packet = udpPacket.Packet(full_packet=current_data)

        if not packet.check_for_corruption():
            stored_packet = False

            for this_packet in finished_packets:
                if this_packet.number == packet.number:
                    confirmation = "Received packet:" + str(packet.number)
                    print("Received duplicate packet:" + str(packet.number))
                    print("Resending confirmation:" + str(packet.number))
                    my_socket.send(confirmation.encode("UTF-8"))
                    stored_packet = True
            for this_packet in waiting_packets:
                if this_packet.number == packet.number:
                    confirmation = "Received packet:" + str(packet.number)
                    print("Received duplicate packet:" + str(packet.number))
                    print("Resending confirmation:" + str(packet.number))
                    my_socket.send(confirmation.encode("UTF-8"))
                    stored_packet = True

            if not stored_packet:
                waiting_packets.append(packet)
                confirmation = "Received packet:" + str(packet.number)
                print(confirmation)
                print("Sending confirmation:" + str(packet.number))
                my_socket.send(confirmation.encode("UTF-8"))
        else:
            print("Dropping bad packet. Not sending confirmation:" + str(packet.number))

        waiting_packets.sort(key=lambda x: x.number)

        for this_packet in waiting_packets:
            if this_packet.number == number_of_packets_written:
                print("Writing packet number " + str(this_packet.number))
                file.write(this_packet.data)
                number_of_packets_written += 1
                finished_packets.append(this_packet)
                waiting_packets.remove(this_packet)
            else:
                continue

    for this_packet in waiting_packets:
        print("Writing packet number " + str(this_packet.number))
        file.write(this_packet.data)

    print("File transfer complete!")
    file.close()
    my_socket.close()
    print("Exiting")
