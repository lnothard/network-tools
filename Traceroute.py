#!/usr/bin/python
# -*- coding: UTF-8 -*-

import threading
import socket
import os
import sys
import struct
import time
import select
import binascii  

TTL_EXCEEDED = 11
ICMP_ECHO_REQUEST = 8 #ICMP type code for echo request messages
ICMP_ECHO_REPLY = 0 #ICMP type code for echo reply messages
MAX_HOPS = 30

ID = 0
ttl = 0

timeout = int (input("Set timeout: "))
print()

def checksum(string): 
	csum = 0
	countTo = (len(string) // 2) * 2  
	count = 0

	while count < countTo:
		thisVal = string[count+1] * 256 + string[count]
		csum = csum + thisVal 
		csum = csum & 0xffffffff  
		count = count + 2
	
	if countTo < len(string):
		csum = csum + string[len(string) - 1]
		csum = csum & 0xffffffff 
	
	csum = (csum >> 16) + (csum & 0xffff)
	csum = csum + (csum >> 16)
	answer = ~csum 
	answer = answer & 0xffff 
	answer = answer >> 8 | (answer << 8 & 0xff00)

	answer = socket.htons(answer)

	return answer
	
def receiveOnePing(icmpSocket, destinationAddress, timeout, sentAt):
	# 1. Wait for the socket to receive a reply
	icmpSocket.settimeout(timeout)
	try:
		data, (addr, port) = icmpSocket.recvfrom(4096)
		receivedAt = time.time()
	except socket.timeout:
		print("* ", end = '')
		return -1, -1, -1
	# 2. Once received, record time of receipt, otherwise, handle a timeout
	# 3. Compare the time of receipt to time of sending, producing the total network delay
	networkDelay = receivedAt - sentAt
	# 4. Unpack the packet header for useful information, including the ID
	unpacked_data = struct.unpack_from("!BBHHH", data[20:28])
	icmp_type = unpacked_data[0]
	# 5. Return total network delay
	return networkDelay, addr, icmp_type
        
def sendOnePing(icmpSocket, destinationAddress):
	# 1. Build ICMP header
	header = struct.pack("!BBHHH", ICMP_ECHO_REQUEST, 0, 0, 1, 1)
	# 2. Checksum ICMP packet using given function
	cs = checksum(header)
	# 3. Insert checksum into packet
	packet = struct.pack("!BBHHH", ICMP_ECHO_REQUEST, 0, cs, 1, 1)
	# 4. Send packet
	icmpSocket.sendto(packet, (destinationAddress, 12645))
	# 5. Record time of sending
	sentAt = time.time()
	return sentAt

def doOnePing(destinationAddress, timeout, ttl): 
	# 1. Create ICMP socket
	sock = socket.socket(
		socket.AF_INET,
		socket.SOCK_RAW,
		socket.IPPROTO_ICMP
	)
	sock.setsockopt(socket.SOL_IP, socket.IP_TTL, ttl)
	# 2. Call sendOnePing function
	sentAt = [0] * 3
	delay = [0] * 3
	sentAt[0] = sendOnePing(sock, destinationAddress)
	sentAt[1] = sendOnePing(sock, destinationAddress)
	sentAt[2] = sendOnePing(sock, destinationAddress)
	# 3. Call receiveOnePing function
	delay[0], addr, icmp_type = receiveOnePing(sock, destinationAddress, timeout, sentAt[0])
	delay[1], addr, icmp_type = receiveOnePing(sock, destinationAddress, timeout, sentAt[1])
	delay[2], addr, icmp_type = receiveOnePing(sock, destinationAddress, timeout, sentAt[2])
	# 4. Close ICMP socket
	sock.close()
	# 5. Return total network delay
	return delay, addr, icmp_type

def ping(host, timeout):
	# 1. Look up hostname, resolving it to an IP address
	ip = socket.gethostbyname(host)
	# 2. Call doOnePing function, approximately every second
	def repeat():
		timer = threading.Timer(2.0, repeat)
		timer.start()
		global ttl
		ttl = ttl + 1
		delay, addr, icmp_type = doOnePing(ip, timeout, ttl)
		# 3. Print out the returned delay
		try:
			if (delay[0] != -1 and delay[1] != -1 and delay[2] != -1):
				(name, x, y) = socket.gethostbyaddr(addr)
				print(ttl, name, "(" + addr + ")", float("{0:.3f}".format(delay[0] * 1000)), "ms", float("{0:.3f}".format(delay[1] * 1000)), "ms", float("{0:.3f}".format(delay[2] * 1000)), "ms")
			else:
				print()
				print(ttl, end = ' ')
		except socket.herror:
			if (delay[0] != -1 and delay[1] != -1 and delay[2] != -1):
				print(ttl, addr, "(" + addr + ")", float("{0:.3f}".format(delay[0] * 1000)), "ms", float("{0:.3f}".format(delay[1] * 1000)), "ms", float("{0:.3f}".format(delay[2] * 1000)), "ms")
			else:
				print()
				print(ttl, end = ' ')		
		
		if (icmp_type == ICMP_ECHO_REPLY):
			timer.cancel()
			os._exit(0)

		if (ttl >= MAX_HOPS):
			timer.cancel()
			os._exit(0)
	# 4. Continue this process until stopped  
	repeat()

ping("lancaster.ac.uk", timeout)


	


