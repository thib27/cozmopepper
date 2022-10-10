# coding: utf-8
import socket
import util_cozmo
import cozmo

ClientMultiSocket = socket.socket()
host = 'localhost'
port = 2004


def main(robot):
    #Connection au serveur
    print('Waiting for connection response')
    try:
        ClientMultiSocket.connect((host, port))
    except socket.error as e:
        print(str(e))
    
    print('Connected , entering loop')
    res = ClientMultiSocket.recv(1024)
    print(res.decode())
    ClientMultiSocket.send(str.encode("cozmo"))
    ClientMultiSocket.recv(1024)
    #Une fois connecté on peut parler au serveur     
    if (util_cozmo.initializeCozmo(robot)):
        print("[COZMO] initialized...")
        print()
        print()
    else: 
        print("[COZMO] initialization problem...")

    while True:
        #on commence toujours par regarder si on a de la donnée sur le serveur(la fonction s'occupe de traiter la réponse )
        util_cozmo.checkData(ClientMultiSocket,robot)

        '''
        #Puis on fais la boucle de traitement de cozmo
        ClientMultiSocket.send("dialog1".encode())
        ClientMultiSocket.recv(1024)
    '''
#__________________________________________________
cozmo.robot.Robot.drive_off_charger_on_connect = False
    
if __name__=='__main__':
    cozmo.run_program(main)
