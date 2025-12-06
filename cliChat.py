__author__ = 'Yoav_Sarig_and_Ido_Keysar'

from sys import argv

import socket
import msvcrt, time
import threading
from tcp_by_size import send_with_size, recv_by_size

input_data = ""

my_score = 0
my_card_num = 150


class input_thread(threading.Thread):
    """
    use global to indicate new command from user
    """

    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        global input_data
        global my_score
        time.sleep(2)
        while input_data != 'q':
            print("Your current score is: " + str(my_score) + "\n Your current number is :" + str(my_card_num))
            print("--------------------")
            print("1: Private message to...\n")
            print("2: Public message...\n")
            print("3: Request other user's number...\n")
            print("4: Request maximum number...\n")
            print("5: Change my number...\n")
            print("6: Exit...\n")
            input_data = craft_message(input("Enter num: "))
            time.sleep(0.2)  # prevent busy waiting

def craft_message(num_str):
    num = int(num_str)
    if num == 1:
        return "PRVM|" + user_name + "|" + input("Enter target: ") + "|" + input("Enter message contents: ")
    elif num == 2:
        return "PUBM|" + user_name + "|" + input("Enter message contents: ")
    elif num == 3:
        return "NUMG|" + input("Enter target user: ")
    elif num == 4:
        return "MAXG"
    elif num == 5:
        return "SWIC|" + input("Enter new num: ")
    elif num == 6:
        return "q"


def main(ip, user_name):
    global input_data
    global my_score
    global my_card_num

    cli_s = socket.socket()
    if not ip or len(ip) < 7:
        ip = "127.0.0.1"
    cli_s.connect((ip, 33446))

    cli_s.settimeout(0.3)

    input_t = input_thread()
    input_t.start()

    while True:
        data = ""
        if input_data == "q":
            break
        if input_data != "":
            data = input_data
            input_data = ""
            fields = data.split("|")
            if (fields[0] == "PRVM"):
                msg = fields[0] + "|" + fields[1] + "|" + fields[2] + "|" + fields[3]
            elif (fields[0] == "PUBM"):
                msg = fields[0] + "|" + fields[1] + "|" + fields[2]
            elif (fields[0] == "NUMG"):
                msg = fields[0] + "|" + fields[1]
            elif (fields[0] == "MAXG"):
                msg = fields[0]
            elif (fields[0] == "SWIC"):
                msg = fields[0] + "|" + fields[1]
            send_with_size(cli_s, msg)

        try:
            data = recv_by_size(cli_s)
            if (data is None or data == ""):
                print("seems server DC")
                break
            print("Got data >>> " + data)
            fields = data.split("|")
            msg_type = data[:4]
            if msg_type == "NAME":
                send_with_size(cli_s, "NAMR|" + user_name + ":" + user_name[::-1])
            elif msg_type == "MSGR":
                print(fields[1] + ": " + fields[2])
            elif msg_type == "NUMR":
                print(f"User {fields[1]} number is: {fields[2]}")

            elif msg_type == "SWIR":
                global my_card_num
                my_card_num = int(fields[1])
                print(f"your num changed to: {my_card_num}")

            elif msg_type == "ERRO":
                print("error") # add err codes

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
