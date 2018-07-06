# Client model
#
import socket
import sys


# define host and port
host = "127.0.0.1"

# Should be same port
port = int(sys.argv[1])

# Socket
client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

client_sock.connect((host, port))

while True:
    message = input("Enter message to server: ")
    message = message.encode('utf-8')
    client_sock.send(message)
