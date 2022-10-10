#This is for socket server
# coding: utf-8
from tkinter import *                                        
from tkinter import filedialog
import socket
import cv2                                        
import time
import MaskRecoFiles.detect_mask_img                                 
import util_serv 
from _thread import *
import threading  


def main():
    ServerSideSocket = socket.socket()
    host = 'localhost'
    port = 2004
    ThreadCount = 0
    try:
        ServerSideSocket.bind((host, port))
    except socket.error as e:
        print(str(e))

    print('Socket is listening..')
    ServerSideSocket.listen(2)
    t1 = 0
    t2 = 0

    #Attendre deux clients
    while ThreadCount <2:
        Client, address = ServerSideSocket.accept()
        print('Connected to: ' + address[0] + ':' + str(address[1]))
        print(address)

        if(ThreadCount == 0):
            t1 = threading.Thread(target=util_serv.multi_threaded_client, args=(Client,))
        if(ThreadCount == 1):
            t2 = threading.Thread(target=util_serv.multi_threaded_client, args=(Client,))

        #start_new_thread(multi_threaded_client, (Client, ))
        ThreadCount += 1
        print('Thread Number: ' + str(ThreadCount))

    print("Starting Threads")
    # start threads
    t1.start()
    t2.start()

    # wait until threads finish their job
    print("Waiting for Threads to finish")
    t1.join()
    t2.join()


    print("Server is closing...")
    ServerSideSocket.close()
    
    
    

if __name__=='__main__':
    main()



