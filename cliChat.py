__author__ = 'YOAV'

from sys import argv

import socket
import msvcrt, time
import threading
from tcp_by_size import send_with_size, recv_by_size

# com1

input_data = ""


class input_thread(threading.Thread):
    """
    use global to indicate new command from user
    """

    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        global input_data
        time.sleep(2)
        while input_data != 'q':
            input_data = input("Enter_data to send>")
            time.sleep(0.2)  # prevent busy waiting


def main(ip, user_name):
    global input_data

    cli_s = socket.socket()
    if not ip or len(ip) < 7:
        ip = "127.0.0.1"
    cli_s.connect((ip, 33446))

    cli_s.settimeout(0.3)
    print("For Private type P:name:<message>\n")

    input_t = input_thread()
    input_t.start()

    while True:
        data = ""
        if input_data == "q":
            break
        if input_data != "":
            data = input_data
            input_data = ""
            if data[:2] == "P:":
                fields = data.split(":")
                msg = "PRVM|" + user_name + "|" + fields[1] + "|" + fields[2]
            else:
                msg = "PUBM|" + user_name + "|" + data
                print(fields[1] + ": " + fields[2])
            send_with_size(cli_s, msg)

        try:
            data = recv_by_size(cli_s)
            if data == "":
                print("seems server DC")
                break
            print("Got data >>> " + data)
            fields = data.split("|")
            msg_type = data[:4]
            if msg_type == "NAME":
                send_with_size(cli_s, "NAMR|" + user_name + ":" + user_name[::-1])
            elif msg_type == "MSGR":
                print(fields[1] + ": " + fields[2])

        except socket.error as err:

            if err.errno == 10035 or str(err) == "timed out":  # if we use conn.settimeout(x)
                continue
            if err.errno == 10054:
                # 'Connection reset by peer'
                print("Error %d Client is Gone. %s reset by peer." % (err.errno, str(cli_s)))
                break
            else:
                print("%d General Sock Error Client %s disconnected" % (err.errno, str(cli_s)))
                break

        except Exception as err:
            print("General Error:", err.message)
            break

    print("Bye Bye from " + user_name)
    cli_s.close()


if __name__ == "__main__":
    if len(argv) < 3:
        print("you must enter <IP> <username>")
        main("127.0.0.1", "user1")
        # exit()
    else:
        ip = argv[1]
        user_name = argv[2]
        main(ip, user_name)
