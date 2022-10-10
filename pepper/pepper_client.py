# coding: utf-8
import socket
import time
from paramiko import util
import util_pepper
import qi
ClientMultiSocket = socket.socket()
host = 'localhost'
port = 2004


def main():
    #Connection au serveur
    print('Waiting for connection response')
    try:
        ClientMultiSocket.connect((host, port))
    except socket.error as e:
        print(str(e))
   
    print('Connected , entering loop')
    res = ClientMultiSocket.recv(1024)
    print(res.decode())
    ClientMultiSocket.send(str.encode("pepper"))
    print(ClientMultiSocket.recv(1024).decode())

    #Préparation des proxys + accès ftp
    
    test=True
    #Une fois connecté on peut parler au serveur 
    util_pepper.pepper_loop(ClientMultiSocket)
    '''  
    while True:
        time.sleep(0.1)
        #on commence toujours par regarder si on a de la donnée sur le serveur(la fonction s'occupe de traiter la réponse )
        util_pepper.checkData(ClientMultiSocket, tts,behavior_mng_service)
        if(test):
            test=False
            ClientMultiSocket.send("distanceNotRespected".encode())
            ClientMultiSocket.recv(1024)

            
        #Puis on fais la boucle de traitement de pepper
        util_pepper.takePicture(photoCaptureProxy,ftp_client)
        ClientMultiSocket.send("imageReady".encode())
        tts.say(str(ClientMultiSocket.recv(1024).decode()))
    
    '''
       
    

if __name__=='__main__':
    main()