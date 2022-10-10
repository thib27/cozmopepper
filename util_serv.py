#Toutes les fonctions utilisées par le serveur 
# coding: utf-8
import collections
from collections import Counter
from tkinter import *
from tkinter import filedialog

import cv2
import time
import sys
import MaskRecoFiles.detect_mask_img
import socket
import os
from _thread import *
import threading
import numpy as np
path="img/image.jpg"    
detect_mask_img =MaskRecoFiles.detect_mask_img
lock = threading.Lock()

#_____________________________________________
#variables
to=""
msg = ""
msgType=""
isSpeaking=False
maskOK=0
masktemp=[]
#_____________________________________________
#Dialogues

#_____________________________________________
#Dialogue test
def dialog1():
    global isSpeaking
    lock.acquire()
    
    if(isSpeaking==False):
        
        isSpeaking=True
        lock.release()
        print("dialogStarted")
        setMsgType("dialog")
        sendMsg("pepper","") 
       
        sendMsg("cozmo","")
       
        setMsgType("msg")
        sendMsg("pepper","hello pepper")
   
        sendMsg("cozmo","bonjour tout le monde")
        
        '''
        setMsgType("covidInfo")
        sendMsg("cozmo","")
        '''

        setMsgType("stop")
        sendMsg("pepper","")
        sendMsg("cozmo","")
       
      
        lock.acquire()
        isSpeaking=False
        lock.release()
        print("dialogOver")
    else:
       
        lock.release()
#Dialogue à créer
def dialog_distance_not_respected():
    global isSpeaking
    lock.acquire()
    
    if(isSpeaking==False):
        
        isSpeaking=True
        lock.release()

        print("dialogStarted")
        setMsgType("dialog")
        sendMsg("pepper","")
        sendMsg("cozmo","")
       
     
        setMsgType("behavior")
    
        sendMsg("cozmo","playAngryAnim")
        time.sleep(2)
        sendMsg("pepper","ecarter")
    
        setMsgType("stop")
        sendMsg("pepper","")
        sendMsg("cozmo","")
       
      
        lock.acquire()
        isSpeaking=False
        lock.release()
        print("dialogOver")
    else:
       
        lock.release()
def dialog_distance_respected():
    global isSpeaking
    lock.acquire()
    
    if(isSpeaking==False):
        
        isSpeaking=True
        lock.release()
        print("dialogStarted")
        setMsgType("dialog")
        sendMsg("pepper","")
        sendMsg("cozmo","")
       
     
        setMsgType("behavior")
        sendMsg("pepper","Happy")
        time.sleep(2)
        sendMsg("cozmo","playHappyAnim")
        
    
        setMsgType("stop")
        sendMsg("pepper","")
        sendMsg("cozmo","")
       
      
        lock.acquire()
        isSpeaking=False
        lock.release()
        print("dialogOver")
    else:
       
        lock.release()
def dialog_mask_off(phrase):
    global path,isSpeaking
    
    lock.acquire()
    
    if(isSpeaking==False):
        
        isSpeaking=True
        lock.release()
        print("dialogNoMaskStarted")
        setMsgType("dialog")
        sendMsg("pepper","")
        sendMsg("cozmo","")
       
     
        setMsgType("msg")
        sendMsg("pepper",phrase)
        setMsgType("behavior")
        time.sleep(2)
        sendMsg("cozmo","maskOff")
        
    
        setMsgType("stop")
        sendMsg("pepper","")
        sendMsg("cozmo","")
       
      
        lock.acquire()
        isSpeaking=False
        lock.release()
        print("dialogOver")
    else:
       
        lock.release()
def dialog_mask_on(phrase):
    global path,isSpeaking
    
    lock.acquire()
    
    if(isSpeaking==False):
        
        isSpeaking=True
        lock.release()
        print("dialogMaskStarted")
        setMsgType("dialog")
        sendMsg("pepper","")
        sendMsg("cozmo","")
       
     
        setMsgType("msg")
        sendMsg("pepper",phrase)
        setMsgType("behavior")
        time.sleep(2)
        sendMsg("cozmo","maskOn")
        
    
        setMsgType("stop")
        sendMsg("pepper","")
        sendMsg("cozmo","")
       
      
        lock.acquire()
        isSpeaking=False
        lock.release()
        print("dialogOver")
    else:
       
        lock.release()

#_____________________________________________
#_____________________________________________
#Fonctions 

#_____________________________________________
#Fonction qui permet de set le type de message 
def setMsgType(msgType1):
    global msgType
    lock.acquire()
    msgType=msgType1
    lock.release()
#_____________________________________________
#Fonction qui permet de set le message et le client à qui il est destiné puis attend que le client l'ai récupéré 

def sendMsg(to1,msg1):
    global to
    global msg
   
    lock.acquire()
    to=to1
    msg=msg1
    lock.release()
    waitDataGone()
#_____________________________________________
#Fonction qui permet de check si le client à un message , si c'est le cas on le lui envoie

def getData(connection,name):
    global to 
    global msg
    global msgType
    
    lock.acquire()
    if(to==name):
            print(msgType)
            connection.send(msgType.encode())
            connection.recv(1024).decode()
            if(msg!=""):
                connection.send(msg.encode())
                connection.recv(1024).decode()
                connection.send("over".encode())
            else:
                connection.send("over".encode())
            to=""
            msg=""
            
    else:
        connection.send("noData".encode())
        connection.recv(1024).decode()
        connection.send("over".encode())
        
    lock.release()


#_____________________________________________
#Fonction qui permet d'attendre que le message contenu dans les variables (msgType,msg et to) ai été envoyé
def waitDataGone():
    global to,msg
    test=True
    
    while(test):
        lock.acquire()
        if(to=="" and msg==""):
            test=False
        lock.release()
# si quelqu'un est arrivé on envoie un message à cozmo pour qu'il se prépare à interagir avec des cubes
def sendOneMsg(to1,msgType1,msg1):
    global lock,to,msg,msgType,isSpeaking
    test=True
    while(test):
        lock.acquire()
        if(isSpeaking==False):
            test=False
        lock.release()
    
    waitDataGone()
    
    lock.acquire()
    isSpeaking=True    
    to=to1
    msgType=msgType1
    msg=msg1
    isSpeaking=False   
    lock.release()
    waitDataGone()
    
#_____________________________________________
#Fonction qui permet de décider quelle phrase envoyer en fonction du nombre de gens et masques portés

def whatToDo(masks):
    global masktemp
    global maskOK
    phrase = " "
   
    if(np.array_equal(np.array(masks),np.array(masktemp))==False):
        
        if(len(masks) == 1):
            if(masks[0] == 0):
                phrase = "Mets un masque s'il te plait"
                maskOK=2
            if(masks[0] == 1):
                phrase = "Merci d'avoir mis ton masque"
                maskOK=1

        if(len(masks) == 2):
            maskOK=2
            if((masks[0] == 0 and masks[1] == 1)or (masks[0] == 1 and masks[1] == 0)):
                phrase = "L'un d'entre vous deux ne porte pas de masque, peux tu en utiliser un s'il te plait"
            if(masks[0] == 0 and masks[1] == 0):
                phrase = "Aucun d'entre vous deux ne porte de masque. Faites quelque chose ou je m'ainerve"
            if(masks[0] == 1 and masks[1] == 1):
                phrase = "Merci de porter un masque tous les deux, c'est sympa"
                maskOK=1
            
        if(len(masks) >2):
            n = Counter(masks)[0]
            if(n == 0):
                phrase = "GG a vous, vous portez tous un masque"
                maskOK=1
            else:
                phrase = "Je n'ai pas peur du virus, mais "+ str(n) + " d'entre vous ne portent pas de masque. Veuillez en porter un s'il vous plait" 
                maskOK=2
        masktemp=masks
    else:
       
        phrase=" "

    return phrase


#_____________________________________________
#Fonction qui permet de décider ce qu'on fait de la donnée que l'on vient de reçevoir du client
def selectAnswer(connection,message,name):
    global to,msg,msgType,isSpeaking
    if(message=="getData"):
        getData(connection,name)

    elif(message == "covidInfo"):
        print("[SERV] Received covid info, sending cozmo -------------")
        connection.send("received".encode())
        t_covidInfo=threading.Thread(target=sendOneMsg,args=("cozmo","covidInfo",""))
        t_covidInfo.start()
                        
    elif(message=="imageReady"):
        #Le serveur analyse si les gens portent un masque
        #Retourne un tableau de la taille du nombre de gens
        #Le tableau comporte des 0 si pas de masque, 1 si masque (gauche à droite)
        connection.send("received".encode())
        #img.ups.upscale()
        #print("Real-time upscaled !")
        tabOfPeople = detect_mask_img.receiveAndCheckImg(path)
        print(tabOfPeople)
        #Prendre une décisison selon le tableau retourné
        phrase = whatToDo(tabOfPeople)
        print(phrase)
        cv2.destroyAllWindows()
        lock.acquire()

        if  isSpeaking==False:
            if maskOK==1:
                lock.release()
                t_noMask = threading.Thread(target=dialog_mask_on, args=(str(phrase),))
                t_noMask.start()
            elif maskOK==2:
                lock.release()
                t_mask = threading.Thread(target=dialog_mask_off, args=(str(phrase),))
                t_mask.start()
            else:
                lock.release()
     
       
        #send un dialogue


    #if(name=="pepper"):
        #Quand le nom du thread est pepper on fait les tests spécifiques à pepper
    #if(name=="cozmo"):
        #Quand le nom du thread est cozmo on fait les tests spécifiques à cozmo
    elif(message=="someoneArrived"):
        connection.send("received".encode())
        t_arrived=threading.Thread(target=sendOneMsg,args=("cozmo","someoneArrived",""))
        t_arrived.start()

    elif(message=="noOneLeft"):
        connection.send("received".encode())
        t_noOne=threading.Thread(target=sendOneMsg,args=("cozmo","goToSleep",""))
        t_noOne.start()
    
        
    
    elif(message=="distanceNotRespected"):
        connection.send("received".encode())
        lock.acquire()
        if  isSpeaking==False:
            lock.release()
            t_notRespected = threading.Thread(target=dialog_distance_not_respected, args=())
            t_notRespected.start()
            
    elif(message=="distanceRespected"):
        connection.send("received".encode())
        lock.acquire()
        if isSpeaking==False:
            lock.release()
            t_respected = threading.Thread(target=dialog_distance_respected, args=())
            t_respected.start()

    elif(message=="dialog1"):
        connection.send("received".encode())
        lock.acquire()
        if  isSpeaking==False:
            lock.release()    
            t3 = threading.Thread(target=dialog1, args=())
            t3.start()
            


#_____________________________________________
#Fonction contenue dans chaque thread "client" du serveur et qui détermine comment le serveur traite les informations
def multi_threaded_client(connection):
    name=""
    while name=="":
        connection.sendall(str.encode('Server is waiting for your name'))
        name = connection.recv(2048).decode()
        
        if(name!="cozmo" and name!="pepper" ):
            name=""
    connection.sendall("keepIt".encode())
    while True:
        message=connection.recv(2048).decode()
        selectAnswer(connection,message,name)

    print("[Thread] finished")
    connection.close()


#_____________________________________________
# run par le server