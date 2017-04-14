import socket
import threading
import signal
import sys


config =  {
            "HOST_NAME" : "0.0.0.0",
            "BIND_PORT" : 12345,
            "MAX_REQUEST_LEN" : 1024,
            "CONNECTION_TIMEOUT" : 5
          }

def HTTP_request_he_to_she(http_request):
    lines = http_request.split('\n')
    index = False
    text = ""
    for i in range(len(lines)) :
        if lines[i] == "" :
            try :
                index = i+1
                text = lines[i+1]
            except IndexError :
                return False

        if "Content-Type: image" in lines[i] :
            return False

    text.replace(" he ", " she ")
    print(text)
    if index != False :
        lines[index] = text
    else :
        return False
    return lines




class Server:
    """ The server class """

    def __init__(self, config):
        signal.signal(signal.SIGINT, self.shutdown)     # Shutdown on Ctrl+C
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)             # Create a TCP socket
        self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)    # Re-use the socket
        self.serverSocket.bind((config['HOST_NAME'], config['BIND_PORT'])) # bind the socket to a public host, and a port
        self.serverSocket.listen(10)    # become a server socket
        self.__clients = {}



    def listenForClient(self):
        """ Wait for clients to connect """
        while True:
            (clientSocket, client_address) = self.serverSocket.accept()   # Establish the connection
            d = threading.Thread(name=self._getClientName(client_address), target=self.proxy_thread, args=(clientSocket, client_address))
            d.setDaemon(True)
            d.start()
        self.shutdown(0,0)


    def proxy_thread(self, conn, client_addr):
        """
        *******************************************
        *********** PROXY_THREAD FUNC *************
          A thread to handle request from browser
        *******************************************
        """

        request_from_browser = conn.recv(config['MAX_REQUEST_LEN'])        # get the request from browser
        request_from_proxy = request_from_browser

        first_line = request_from_browser.split('\n')[0]  
        print("######################")
        print(first_line[:50])
        try :                 # parse the first line
            url = first_line.split(' ')[1]   
        except IndexError :
            url = ""                     # get url
        print(url[:50])
        print("######################")
        # find the webserver and port
        http_pos = url.find("://")          # find pos of ://
        if (http_pos==-1):
            temp = url
        else:
            temp = url[(http_pos+3):]       # get the rest of url

        port_pos = temp.find(":")           # find the port pos (if any)

        # find end of web server
        webserver_pos = temp.find("/")
        if webserver_pos == -1:
            webserver_pos = len(temp)

        webserver = ""
        port = -1
        if (port_pos==-1 or webserver_pos < port_pos):      # default port
            port = 80
            webserver = temp[:webserver_pos]
        else:                                               # specific port
            port = int((temp[(port_pos+1):])[:webserver_pos-port_pos-1])
            webserver = temp[:port_pos]

        try:
            # create a socket to connect to the web server
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(config['CONNECTION_TIMEOUT'])
            s.connect((webserver, port))
            s.sendall(request_from_proxy)                           # send request to webserver

            while 1:
                data_from_server = s.recv(config['MAX_REQUEST_LEN'])          # receive data from web server
                data_from_proxy = data_from_server
                #HTTP_request_he_to_she(data_from_proxy)
                if (len(data_from_proxy) > 0):
                    conn.send(data_from_proxy)                               # send to browser
                else:
                    break
            s.close()
            conn.close()
        except socket.error as error_msg:
            print 'ERROR: ',client_addr,error_msg
            if s:
                s.close()
            if conn:
                conn.close()


    def _getClientName(self, cli_addr):
        """ Return the clientName.
        """
        return "Client"


    def shutdown(self, signum, frame):
        """ Handle the exiting server. Clean all traces """
        self.serverSocket.close()
        sys.exit(0)


if __name__ == "__main__":
    print("the program is starting")
    server = Server(config)
    
    server.listenForClient()

