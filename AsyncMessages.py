
import threading


# this is a commit

class AsyncMessages():
    """
        this class provide global messages area for server that handle muktyclients by threads
        it enable many threads to communicate by one dictionary (self.async_msgs)
        each thread might put data to specific other thread (the key is the other thread socket)
        each thread can get his messages by his socket
        this class is thread safe
    """

    def __init__(self):
        self.lock_async_msgs = threading.Lock()
        self.async_msgs = {}
        self.sock_by_user = {}

    def add_new_socket(self, new_client_sock):
        """
            call to this method right after socket accept with client socket
        """
        self.async_msgs [new_client_sock] = []


    def delete_socket(self, sock):
        """
            cwhen dissconnect
        """
        del self.async_msgs [sock]
        
    def put_msg_in_async_msgs(self,data, other_sock):
        self.lock_async_msgs.acquire()
        self.async_msgs[other_sock].append(data)
        self.lock_async_msgs .release()

    def put_msg_by_user(self,data, user):
        self.lock_async_msgs.acquire()
        self.async_msgs[self.sock_by_user[user]].append(data)
        self.lock_async_msgs .release()
        
    def put_msg_to_all(self,data):
        self.lock_async_msgs.acquire()
        for s in self.async_msgs.keys():
            self.async_msgs[s].append(data)
        self.lock_async_msgs.release()
            

    def get_async_messages_to_send(self, my_sock):
        msgs = []
        if self.async_msgs [my_sock] != []:
            self.lock_async_msgs .acquire()
            msgs =  self.async_msgs[my_sock]
            self.async_msgs[my_sock] = []
            self.lock_async_msgs .release()
        return msgs


