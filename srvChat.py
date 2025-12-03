__author__ = 'Yossi'
import socket
import time
import threading

from  tcp_by_size import send_with_size ,recv_by_size
from AsyncMessages import AsyncMessages

async_msg = None
 
EWOULDBLOCK = 10035

def handle_message(data, user_name):
    global async_msg

    to_send = ""

    fields = data.split("|")
    msg_type = fields[0]

    if msg_type == "PUB":
        from_user = fields[1]
        public_msg = fields[2]
        for user in async_msg.sock_by_user.keys():
            if user != user_name:
                async_msg.put_msg_by_user("MSG|" + from_user + "|" + public_msg,user)
    if msg_type == "PRV":
        from_user = fields[1]
        to_user = fields[2]
        msg = fields[3]
        async_msg.put_msg_by_user("MSG|" + from_user + "|" + msg,to_user)

    return to_send

def check_user_pass(u,p):
    """
    check in some db user and password
    :param u:
    :param p:
    :return:
    """
    print ("name:" + u + " pass:" + p + " checked")
    return True


def handl_client(sock , tid):
    """
    main thread - recv handle and answer also push async msgs
    :param sock: socket
    :param tid: thread is
    :return:
    """
    global async_msg

    user_name = ""
    exit_thread = False

    print ("New Client num " + str(tid))
    to_send = "NAM|<uname>:<pass>"

    got_name = False;
    while not got_name:
        send_with_size(sock,to_send)
        data = recv_by_size(sock)
        if data == "":
            print ("Client disconnected")
            exit_thread = True
            break
        if data[:3] == "NMR" and len(data) > 6 :
            got_name = True
            fields = data[4:].split(':')
            user_name =  fields[0]
            password = fields[1]
            if check_user_pass(user_name,password):
                async_msg.sock_by_user[user_name] = sock
            else:
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
