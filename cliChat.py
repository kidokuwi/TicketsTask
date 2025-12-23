__author__ = 'Yoav_Sarig_and_Ido_Keysar'

import random
from operator import truediv
from sys import argv

import socket
import msvcrt, time
import threading
from tcp_by_size import send_with_size, recv_by_size

input_data = ""
lock = threading.Lock()
my_card_num = 150
users_nums = {}
continuee = True
user_nameglob = ""

class input_thread(threading.Thread):
    """
    use global to indicate new command from user
    """

    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        global input_data
        global users_nums
        time.sleep(2)
        while input_data != 'q' and continuee:
            print("Your current score is: " + str(sum(users_nums)) + "\nYour current number is: " + str(my_card_num))
            print("--------------------")
            print("1: Private message to...\n")
            print("2: Public message...\n")
            print("3: Request other user's number...\n")
            print("4: Request maximum number...\n")
            print("5: Change my number...\n")
            print("6: Exit...\n")
            response = input("Enter your choice: ")
            if (response.isdigit()):
                input_data = craft_message(response)
            else:
                print("Invalid input, please try again")
            time.sleep(0.2)

def craft_message(num_str):
    global user_nameglob
    num = int(num_str)
    if num == 1:
        return "PRVM|" + user_nameglob + "|" + input("Enter target: ") + "|" + input("Enter message contents: ")
    elif num == 2:
        return "PUBM|" + user_nameglob + "|" + input("Enter message contents: ")
    elif num == 3:
        return "NUMG|" + input("Enter target user: ")
    elif num == 4:
        return "MAXG"
    elif num == 5:
        inpt = input("Enter new num: ")
        while not inpt.isdigit():
            inpt = input("Invalid input. Please enter a number: ")
        return "SWIC|" + inpt
    elif num == 6:
        return "q"


def main(ip, user_name):
    global input_data
    global continuee
    global my_card_num
    global user_nameglob
    user_nameglob = user_name
    my_card_num = random.randint(1,999)

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
            msg = fields[0]
            if msg == "PRVM":
                msg = msg + "|" + fields[1] + "|" + fields[2] + "|" + fields[3]
            elif msg == "PUBM":
                msg = msg + "|" + fields[1] + "|" + fields[2]
            elif msg == "NUMG":
                msg = msg + "|" + fields[1]
            elif msg == "MAXG":
                msg = msg
            elif msg == "SWIC":
                msg = msg + "|" + fields[1]
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
                msg = "NAMR|" + user_name + ":" + user_name[::-1] + ":" + str(my_card_num)
                send_with_size(cli_s, msg)
            elif msg_type == "MSGR":
                print(fields[1] + ": " + fields[2])
            elif msg_type == "NUMR":
                print(f"User {fields[1]} number is: {fields[2]}")
                if (user_name != fields[1]):
                    users_nums[fields[1]] = int(fields[2])
                    print("Updated users numbers:", users_nums)
                    print("Current sum of all users numbers is: ", sum(users_nums))
                    if (sum(users_nums) > 2000):
                        msg = "IWIN|" + user_name
                        send_with_size(cli_s, msg)
                else:
                    print("received own number, not updating users_nums")
            elif msg_type == "SWIR":
                lock.acquire()
                my_card_num = int(fields[1])
                lock.release()
                print(f"your num changed to: {my_card_num}")
            elif msg_type == "WINN":
                print(f"User {fields[1]} has won the game!")
                continuee = False
            elif msg_type == "EROR":
                lock.acquire()
                if fields[1] == "001":
                    print("General server error")
                elif fields[1] == "002":
                    print("Your user name already exists in server. Retry with another")
                    continuee = False
                    input_t.join()
                lock.release()

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

def sum(user_nums):
    s = 0
    for n in user_nums.values():
        s += n
    return s

if __name__ == "__main__":
    if len(argv) < 3:
        print("you must enter <IP> <username>")
        main("127.0.0.1", "user1")
        # exit()
    else:
        ip = argv[1]
        user_nameglob = argv[2]
        main(ip, user_nameglob)
