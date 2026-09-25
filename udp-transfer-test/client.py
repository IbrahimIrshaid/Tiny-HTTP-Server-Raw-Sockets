from socket import *
serverName = "127.0.0.1"
serverPort = 8090
clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect((serverName,serverPort))
sentence = input('Enter "Start" to Initiat Connection\n')
clientSocket.send(sentence.encode())

udp_sock = socket(AF_INET, SOCK_DGRAM)

for i in range(1000001):
    udp_sock.sendto(str(i).encode(), (serverName,serverPort))


udp_sock.close()
clientSocket.send(b"END")
clientSocket.close()
