__author__ = 'Yoav_Sarig_and_Ido_Keysar'
import socket
import time
import threading

from  tcp_by_size import send_with_size ,recv_by_size
from AsyncMessages import AsyncMessages

async_msg = None
user_nums = {}

EWOULDBLOCK = 10035

def handle_message(data, user_name):
    global async_msg
    global user_nums

    to_send = ""

    fields = data.split("|")
    msg_type = fields[0]

    if msg_type == "PUBM":
        from_user = fields[1]
        public_msg = fields[2]
        for user in async_msg.sock_by_user.keys():
            if user != user_name:
                async_msg.put_msg_by_user("MSGR|" + from_user + "|" + public_msg,user)
    elif msg_type == "PRVM":
        from_user = fields[1]
        to_user = fields[2]
        msg = fields[3]
        async_msg.put_msg_by_user("MSGR|" + from_user + "|" + msg,to_user)
    elif msg_type == "NUMG":
        target_user = fields[1]
        if target_user in user_nums:
            async_msg.put_msg_by_user("NUMR|" + target_user + "|" + str(user_nums[target_user]), user_name)
        else:
            async_msg.put_msg_by_user("EROR|2|" + target_user, user_name)
    elif msg_type == "MAXG":
        max_user = max(user_nums, key=user_nums.get) if user_nums else "None"
        max_num = user_nums.get(max_user, 0)
        async_msg.put_msg_by_user("NUMR|" + max_user + "|" + str(max_num), user_name)
    elif msg_type == "SWIC":
        new_num_str = fields[1]
        if new_num_str.isdigit():
            user_nums[user_name] = int(new_num_str)

            response_msg = "SWIR|" + new_num_str
            async_msg.put_msg_by_user(response_msg, user_name)
        else:
            response_msg = "EROR|3"
            async_msg.put_msg_by_user(response_msg, user_name)
    elif msg_type == "IWIN":
        async_msg.put_msg_to_all("WINN|"+ user_name)


    return to_send

def check_user_pass(u,p):
    """
    check in some db user and password
    :param u:
    :param p:
    :return:
    """
    return True


def handl_client(sock , tid):
    """
    main thread - recv handle and answer also push async msgs
    :param sock: socket
    :param tid: thread is
    :return:
    """
    global async_msg
    global user_nums

    user_name = ""
    exit_thread = False

    print ("New Client num " + str(tid))
    to_send = "NAME|<uname>:<pass>"

    got_name = False;
    while not got_name:
        send_with_size(sock,to_send)
        data = recv_by_size(sock)
        if data == "" or data is None:
            print ("Client disconnected")
            exit_thread = True
            break
        if data[:4] == "NAMR" and len(data) > 6 :
            got_name = True
            fields = data[5:].split(':')
            if len(fields) >= 3:
                user_name = fields[0]
                password = fields[1]
                card_num_str = fields[2]
                if check_user_pass(user_name, password):
                    print(user_name in async_msg.sock_by_user.keys())
                    if user_name in async_msg.sock_by_user.keys():
                        print("User already exists")
                        send_with_size(sock,"EROR|1")
                        exit_thread = True
                    elif card_num_str.isdigit():
                        user_nums[user_name] = int(card_num_str)
                        print(f"User {user_name} logged in with number: {user_nums[user_name]}")
                        async_msg.sock_by_user[user_name] = sock
                    else:
                        print(f"Login failed: Card number received was invalid: {card_num_str}")
                        exit_thread = True
                else:
                    exit_thread = True
            else:
                print("Login failed: NAMR message format incorrect.")
                exit_thread = True
    sock.settimeout(0.3)

    while not exit_thread :
        try:

            data = recv_by_size(sock)
            if data == "":
                print ("Error: Seems Client DC")
                break

            to_send = handle_message(data,user_name)
            if to_send != "":
                send_with_size(sock,to_send)

        except socket.error as err:

            if err.errno == EWOULDBLOCK or str(err) == "timed out":  # if we use conn.settimeout(x)
                msgs = async_msg.get_async_messages_to_send(sock)
                for data in msgs:
                    send_with_size(sock,data)
                    time.sleep(0.1)
                continue

            if err.errno == 10054:
                #'Connection reset by peer'
                print ("Error %d Client is Gone.  reset by peer." % (err.errno))
                break
            else:
                print ("%d General Sock Error Client disconnected" % (err.errno))
                break

        except Exception as err:
            print ("General Error:", err.message)
            break
    async_msg.delete_socket(sock)
    sock.close()



def main ():
    global async_msg;

    s = socket.socket()
    async_msg = AsyncMessages()
    s.bind(("0.0.0.0", 33446))
    s.listen(4)
    print ("after listen")

    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    threads = []
    i = 1
    while True:
        cli_s , addr = s.accept()
        async_msg.add_new_socket(cli_s)

        t = threading.Thread(target = handl_client, args=(cli_s, i))
        t.start()
        i+=1
        threads.append(t);

    for t in threads:
        t.join()
    s.close()
    print ("Bye ..")



if __name__ == "__main__":
    main()
