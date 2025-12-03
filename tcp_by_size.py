import socket,struct

SIZE_HEADER_FORMAT = "000000000|" # n digits for data size + one delimiter
size_header_size = len(SIZE_HEADER_FORMAT)
TCP_DEBUG = True
        

def recv_by_size(sock, return_type="string"):
    str_size = b""
    data_len = 0
    while len(str_size) < size_header_size:
        _d = sock.recv(size_header_size - len(str_size))
        if len(_d) == 0:
            str_size = b""
            break
        str_size += _d
    data  = b""
    str_size = str_size.decode()
    if str_size != "":
        data_len = int(str_size[:size_header_size - 1])
        while len(data) < data_len:
            _d = sock.recv(data_len - len(data))
            if len(_d) == 0:
                data = b""
                break
            data += _d

    if TCP_DEBUG and len(str_size) > 0:
        data_to_print = data[:100]
        if type(data_to_print) == bytes:
            try:
                data_to_print = data_to_print.decode()
            except (UnicodeDecodeError, AttributeError):
                pass
        print(f"\nSent({str_size})>>>{data_to_print}")

    if data_len != len(data):
        data=b"" # Partial data is like no data !
    if return_type == "string":
        return data.decode()
    return data


def send_with_size(sock, data):
    len_data = len(data)
    len_data = str(len(data)).zfill(size_header_size - 1) + "|"
    len_data = len_data.encode()
    if type(data) != bytes:
        data = data.encode()
    data = len_data + data
    sock.send(data)

    if TCP_DEBUG and len(len_data) > 0:
        data = data[:100]
        if type(data) == bytes:
            try:
                data = data.decode()
            except (UnicodeDecodeError, AttributeError):
                pass
        print(f"\nSent({len_data})>>>{data}")



def __hex(s):
    cnt = 0
    for i in range(len(s)):
        if cnt % 16 == 0:
            print ("")
        elif cnt % 8 ==0:
            print ("    ",end='')
        cnt +=1
        print ("%02X" % int(ord(s[i])),end='')


"""
#
#
#
Binary Size by 4 bytes   from 1 to 4GB
#
#
#
"""



def send_one_message(sock, data):
    """
    Send a message to the socket.
    """
    #sock.sendall(struct.pack('!I', len(message)) + message)
    try:
        length = socket.htonl(len(data))
        if type(data) != bytes:
            data = data.encode();
        sock.sendall(struct.pack('I', length) + data)
        data_part = data[:100]
        if TCP_DEBUG  and len(data) > 0:
            print(f"\nSent({len(data)})>>>{data_part}")
    except:
        print(f"ERROR in send_one_message")
   

def recv_one_message(sock, return_type="string"):
    """
    Recieve one message by two steps 4 bytes and all rest.
    """
    len_section = __recv_amount(sock, 4)
    if not len_section:
        return None
    len_int, = struct.unpack('I', len_section)
    len_int = socket.ntohl(len_int)
    
    data =  __recv_amount(sock, len_int)
    if TCP_DEBUG and len(data) != 0:
        print(f"\nRecv({len_int})>>>{data[:100]}")

    if len_int != len(data):
        data=b'' # Partial data is like no data !
    if return_type == "string":
        return data.decode()
      
    return data


def __recv_amount(sock, size=4):
    buffer = b''
    while size:
        new_bufffer = sock.recv(size)
        if not new_bufffer:
            return b''
        buffer += new_bufffer
        size -= len(new_bufffer)
    #__hex(buffer)
    return buffer 










"""
Unit Test Section
just for test 
"""

        
        
def main_for_test(role):
    import socket
    import time
    port = 12312
    if role == 'srv':
        s= socket.socket()
        s.bind(('0.0.0.0',port))
        s.listen(1)
        cli_s , addr = s.accept()
        data = recv_by_size(cli_s)
        print ("1 server got:" + data)
        send_with_size(cli_s,"1 back:" + data)
        time.sleep(3)
        
        
        print ("\n\n\nServer Binary Sction\n")
        data = recv_one_message(cli_s)
        print ("2 server got:" + data)
        send_one_message(cli_s,"2 back:" + data)
                
        cli_s.close()
        time.sleep(3)
        s.close()
    elif role == 'cli':
        c = socket.socket()
        c.connect(('127.0.0.1',port))
        send_with_size(c,"ABC")

        print ("1 client got:" + recv_by_size(c))
        time.sleep(3)
        
        
        
        
        print ("\n\n\nClient Binary Sction\n")
        send_one_message(c,"abcdefghijklmnop")
        
        print ("2 client got:" + recv_one_message(c))
        time.sleep(3)
        c.close()


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 2 :
        main_for_test(sys.argv[1])
