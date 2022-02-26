#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import socket
import sys
import os

def proxy(tcpSocket):
    # Receive data and decode it
    data = tcpSocket.recv(2048).decode()
    # Get the URL from the received data
    url = data.split('\n')[0].split(' ')[1]
    # Find where the address begins
    http = url.find("://")
    # Get the web address, excluding the '://'
    temp = url[(http + 3):]
    # Get the location of the port number
    portLoc = temp.find(":")
    # Get the location of the server
    serverLoc = temp.find("/")

    if (serverLoc == -1):
        # If not found, make it after the address
        serverLoc = len(temp)

    if (portLoc == -1 or serverLoc < portLoc):
        # If port location not found, use 80 as default port
        port = 80
        server = temp[:serverLoc]
    else:
        port = int((temp[(portLoc + 1):])[:serverLoc - portLoc - 1])
        server = temp[:portLoc]

    # Make a new socket
    newSocket = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM,
        socket.IPPROTO_TCP
    )

    # Connect to the server on the new socket
    newSocket.connect((server, port))
    # Send the data back to the original socket
    newSocket.send(data.encode())

    while 1:
        data = newSocket.recv(2048)

        if (len(data) > 0):
            tcpSocket.send(data)
        else:
            break

    newSocket.close()
    tcpSocket.close()

def startServer(serverAddress, serverPort):
    # 1. Create server socket
    sock = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM,
        socket.IPPROTO_TCP
    )
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # 2. Bind the server socket to server address and server port
    sock.bind((serverAddress, serverPort))
    # 3. Continuously listen for connections to server socket
    sock.listen(1)
    # 4. When a connection is accepted, call handleRequest function, passing new connection socket (see https://docs.python.org/3/library/socket.html#socket.socket.accept)
    conn, address = sock.accept()
    proxy(conn)
    # 5. Close server socket
    sock.close()

port = int (input("Enter the port number to use: "))
startServer("127.0.0.1", port)
