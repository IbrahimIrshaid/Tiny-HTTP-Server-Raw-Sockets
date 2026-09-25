from socket import *
serverPort = 8090
serverSocket = socket(AF_INET,SOCK_STREAM)
serverSocket.bind(('',serverPort))
serverSocket.listen(1)
print ('The server is ready to receive')
FirstSentence = ""
SecSentence = ""
while True:
	connectionSocket, addr = serverSocket.accept()
	FirstSentence = connectionSocket.recv(2048).decode().strip()
	if FirstSentence.lower() == "start":
		print('Listening...\n')
		
		udp_count, wrong_order, lastNum = 0, 0, None

		udp_sock = socket(AF_INET, SOCK_DGRAM)
		udp_sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
		udp_sock.bind(('', serverPort))
		s = ""
		while s != "1000000":
			udp_sock.settimeout(2.0)

			try:
				data, addr2 = udp_sock.recvfrom(2048)
			except timeout:
				print("UDP timeout: stopped receiving (maybe packet loss).")
				break


			s = data.decode().strip()
			udp_count += 1

			# parse integer
			num = int(s)

			if lastNum is not None:
				if num != lastNum + 1:
					wrong_order += 1

			lastNum = num

			
		udp_sock.close()

		print("Total received (UDP): ", udp_count)
		print("Wrong order count: ", wrong_order)
        
	elif SecSentence.lower() == "end":
		print("Closing Connection\n")
		connectionSocket.close()
		serverSocket.close()
	
	SecSentence = connectionSocket.recv(2048).decode().strip()
	if SecSentence.lower() == "end":
		print("Closing Connection\n")
		connectionSocket.close()
		serverSocket.close()
		break
	else:
		print("Waiting for Action...\n")
	
	connectionSocket.close()
