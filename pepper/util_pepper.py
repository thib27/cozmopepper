# coding: utf-8
import os, sys
import socket
import time
import math
import paramiko
import qi
from naoqi import ALProxy

IP = ""
PORT = 9559

#Variables théo
    
varJustArrived = False
varJustLeft = False
groupDistancesOK = False
soloDistancesOK = False
#Utilisé pour laisser un temps de cool down et dans le but de mettre le programme plus lent pour debug
refreshSpeed = 0.01

#Prend une photo et la stocke dans le dossier img 
def set_photo_proxy():
    photoCaptureProxy = ALProxy("ALPhotoCapture", IP, PORT)
    photoCaptureProxy.setResolution(2)
    photoCaptureProxy.setPictureFormat("jpg")
    return(photoCaptureProxy)
def set_tts_proxy():
    tts = ALProxy("ALTextToSpeech", IP, PORT)
    tts.setLanguage("French")
    tts.setVolume(0.6)
    return(tts)
def set_behavior_proxy():
    behavior_mng_service=ALProxy("ALBehaviorManager", IP, PORT)
    return(behavior_mng_service)

def open_ftp():
    ssh_client=paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(hostname=IP,username="nao",password="PepperISEN")
    ftp_client=ssh_client.open_sftp()
    return(ftp_client)
def takePicture(photoCaptureProxy,ftp_client):
    # Create a proxy to ALPhotoCapture
    photoCaptureProxy.takePictures(1, "/home/nao/recordings/cameras/", "image")
    ftp_client.get("recordings/cameras/image.jpg","../img/image.jpg")
    

#Cette fonction est appelée pour préparer pepper à recevoir un dialogue
#quand le serveur envoie "stop" on quitte cette boucle
def treatDialog(ClientMultiSocket, tts,behavior_mng_service):
    while True:
        
        ClientMultiSocket.send("getData".encode())
        res = ClientMultiSocket.recv(1024).decode()
        ClientMultiSocket.send("keepIt".encode())
        if res!="noData":
            print("[pepper] res : "+ res)
            if(res=="msg"):
                
                res = ClientMultiSocket.recv(1024).decode()
                ClientMultiSocket.send("keepIt".encode())
                ClientMultiSocket.recv(1024).decode()
                print(res)
                tts.say(str(res))
            if(res=="behavior"):
                print("[pepper] Behaviour ok")
                res = ClientMultiSocket.recv(1024).decode()
                ClientMultiSocket.send("keepIt".encode())
                ClientMultiSocket.recv(1024).decode()
                
                if(res=="ecarter"):
                    print("pepper ecarte!")
                    behavior_mng_service.runBehavior("custom_applications/eloigner")
                   
            if(res=="stop"):
                   
                ClientMultiSocket.recv(1024).decode()
                print("dialogue fini")
                break
            
        else:
            ClientMultiSocket.recv(1024).decode()
            
#Cette fonction est appelée à chaque début de boucle, elle reçoit une information du serveur . 
#Si elle est différente de noData on décide de ce qu'on fait d'elle
     
def checkData(ClientMultiSocket, tts, behavior_mng_service):
    ClientMultiSocket.send("getData".encode())
    res = ClientMultiSocket.recv(1024).decode()
    if(res!="noData"):
        ClientMultiSocket.send("keepIt".encode())
        ClientMultiSocket.recv(1024).decode()
        if(res=="dialog"):
           
            treatDialog(ClientMultiSocket,tts,behavior_mng_service )
            
    else:
        ClientMultiSocket.send("keepIt".encode())
        res=ClientMultiSocket.recv(1024).decode()


#__________________________________________________________
#Fonctions de théo
#__________________________________________________________
#oneMeter : True si distance respectée, False sinon
def oneMeter(value_service, personne1, personne2):
    FOV = 100
    angle1 = value_service.getData("PeoplePerception/Person/"+str(personne1)+"/AnglesYawPitch")[0] * FOV / 2
    angle2 = value_service.getData("PeoplePerception/Person/"+str(personne2)+"/AnglesYawPitch")[0] * FOV / 2
    
    #Calcul angle qui les séparent
    if(angle1>=0 and angle2>=0):
        angleTot = abs(max(angle1,angle2)) - abs(min(angle1,angle2))
    elif(angle1<0 and angle2<0):
        angleTot = abs(min(angle1,angle2)) - abs(max(angle1,angle2))
    else:
        angleTot = abs(angle1) + abs(angle2)
    
    distance1 = value_service.getData("PeoplePerception/Person/"+str(personne1)+"/Distance")
    distance2 = value_service.getData("PeoplePerception/Person/"+str(personne2)+"/Distance")

    a = min(distance1, distance2)   #Dist humain le plus proche
    b = math.cos(math.radians(angleTot))*a    #Distance à angle droit
    c = math.sin(math.radians(angleTot))*a    #Distance angle droit dist humain le plus loin et humain le plus proche
    d = max(distance1,distance2)    #Dist humain le plus loin
    e = math.sqrt(((d-b)*(d-b))+(c*c))  #Distance entre les 2 personnes
    print("DISTANCE ENTRE PERSONNES = "+str(e))
    if(e>1):
        return True
    else:
        return False

#__________________________________________________________
#groupDistancesOK : True si tout le monde est assez éloigné, False sinon
def checkGroupDistancesOK(peopleList, value_service):
    global groupDistancesOK
    for j in range(len(peopleList)-1):
        for k in range(j+1,len(peopleList)):
            if(oneMeter(value_service, peopleList[j], peopleList[k])):  #Si personne j est éloignée de au moins 1m de la personne k on ne fait rien
                groupDistancesOK = True
            else:
                groupDistancesOK = False
                return False
    return True

#__________________________________________________________
#onJustArrived : signal appelé quand l'événement justArrived est détecté
def onJustArrived(id):
    global varJustArrived
    print
    print("JUSTARRIVED")
    print
    varJustArrived = True
    

#__________________________________________________________
#onJustLeft : signal appelé quand l'événement justLeft est détecté
def onJustLeft(id):
    global varJustLeft
    print
    print("JUSTLEFT")
    print
    varJustLeft = True
#__________________________________________________________
#main
def pepper_loop(ClientMultiSocket):
    global varJustLeft
    global varJustArrived
    global groupDistancesOK
    global soloDistancesOK
    global refreshSpeed
    session = qi.Session()
    session.connect("tcp://" + IP + ":" + str(PORT))
    faceSize=0.1
    # Get the services
    ftp_client=open_ftp()

    photoCaptureProxy=set_photo_proxy()
    behavior_mng_service=set_behavior_proxy()
    motion_service = ALProxy("ALMotion", IP, PORT)
    tracker_service = ALProxy("ALTracker", IP, PORT)
    trackerProxy_service = ALProxy("ALTracker", IP, PORT)
    speaker_service = set_tts_proxy()
    value_service = ALProxy("ALMemory", IP, PORT)
    peoplePerceptionNP_service = session.service("ALPeoplePerception")
    peoplePerception_service = ALProxy("ALPeoplePerception", IP, PORT)
    engZones_service = ALProxy("ALEngagementZones", IP, PORT)
    
    # Start people perception service
    peoplePerception_service.subscribe("perception", 500, 0.0)

    print("I'm starting to look for people")

    # Start engagement zones service
    engZones_service.subscribe("zones", 500, 0.0)

    #Set speaking langage
 
    # First, wake up.
    motion_service.wakeUp()

    # Add target to track.
    targetName = "Face"
    faceWidth = faceSize
    tracker_service.registerTarget(targetName, faceWidth)

    justarrived_signal = peoplePerceptionNP_service.justArrived
    justarrived_connection = justarrived_signal.connect(onJustArrived)
    justleft_signal = peoplePerceptionNP_service.justLeft
    justleft_connection = justleft_signal.connect(onJustLeft)

    # Then, start tracker.
    print ("############################################################")
    print ("Use Ctrl+c to stop this script.")

    isWatchingSomeone = False   #Assuming we are not seeing anyone when the programm starts

    print("ZONES :")
    print("Z1DIST = "+str(engZones_service.getFirstLimitDistance()))
    print("Z2DIST = "+str(engZones_service.getSecondLimitDistance()))
    print("ANGLE = "+str(engZones_service.getLimitAngle()))
    print

    try:
        while True:    
            print("Boucle while TRUE")
            
            while isWatchingSomeone==False:
                checkData(ClientMultiSocket, speaker_service,behavior_mng_service)
                print("Boucle isWatchingSomeone == FALSE")
                tracker_service.track(targetName)
                time.sleep(refreshSpeed)   #Pause dans l'actualisation pour économie de ressources
                #trackerProxy_service.toggleSearch(True)
                if (trackerProxy_service.isSearchEnabled()):
                    print("Recherche active")
                elif (trackerProxy_service.isSearchEnabled()==False):
                    print("Recherche inactive")
                if trackerProxy_service.isNewTargetDetected():
                    trackerProxy_service.toggleSearch(False)
                    tracker_service.stopTracker()
                    print("Personne detectee")
                    isWatchingSomeone = True
            
            print
            print("SORTIE Boucle isWatchingSomeone == FALSE")
            print

            if(isWatchingSomeone):
                ClientMultiSocket.send("someoneArrived".encode())
                ClientMultiSocket.recv(1024)  
            #isWatchingSomeone = True   #DEBUG
            while isWatchingSomeone:
                print("Boucle isWatchingSomeone == TRUE")
                checkData(ClientMultiSocket, speaker_service,behavior_mng_service)
                takePicture(photoCaptureProxy,ftp_client)
                ClientMultiSocket.send("imageReady".encode())
                ClientMultiSocket.recv(1024).decode()
                time.sleep(refreshSpeed)   #Actualisation toutes les x secondes
                print
                peopleList = value_service.getData("PeoplePerception/VisiblePeopleList")

                print(peopleList)
                print("Personnes detectees="+str(len(peopleList))+".")
                #speaker_service.say("Il y a "+len(peopleList)+" personnes devant moi.")
                for i in peopleList:
                    tmpDist = value_service.getData("PeoplePerception/Person/"+str(i)+"/Distance")
                    tmpAngles = value_service.getData("PeoplePerception/Person/"+str(i)+"/AnglesYawPitch")
                    tmpHeight = value_service.getData("PeoplePerception/Person/"+str(i)+"/RealHeight")
                    tmpSColor = value_service.getData("PeoplePerception/Person/"+str(i)+"/ShirtColor")
                    tmpZone = value_service.getData("PeoplePerception/Person/"+str(i)+"/EngagementZone")
                    print("ID["+str(i)+"] : Dist="+str(tmpDist)+"m ; Coordonnees="+str(tmpAngles)+" ; Habit="+str(tmpSColor)+" ; Taille="+str(tmpHeight)+"m ; Zone="+str(tmpZone)+".")
                 
                if (len(peopleList)>1):
                    print("Debut5")
                    if (checkGroupDistancesOK(peopleList, value_service)):
                        groupDistancesOK = True
                        sentence = ("Bonjour à tous ! Vous êtes tous suffisemment écartés, c'est parfait !")
                        print("Debut1")
                        ClientMultiSocket.send("distanceRespected".encode())
                        ClientMultiSocket.recv(1024)
                        print("Fin1")
                    else:
                        groupDistancesOK = False
                        sentence = ("Bonjour à tous ! Faites attention à vos distances, éloignez-vous par mesure de sécurité !")
                        print("Debut2")
                        ClientMultiSocket.send("distanceNotRespected".encode())
                        ClientMultiSocket.recv(1024)
                        print("Fin2")
                    #speaker_service.say(sentence)
                    print("Fin5")

                elif (len(peopleList)==1):
                    print("Debut3")
                    soloDistancesOK = True
                    sentence = ("Bonjour ! Vous êtes à "+str(round(value_service.getData("PeoplePerception/Person/"+str(peopleList[0])+"/Distance"),1))+" mètres de moi, c'est parfait !")
                    if (value_service.getData("PeoplePerception/Person/"+str(peopleList[0])+"/Distance")<1):
                        sentence = ("Bonjour ! Faites attention à vos distances, vous êtes à "+str(round(value_service.getData("PeoplePerception/Person/"+str(peopleList[0])+"/Distance"),1))+" mètres de moi !")
                        soloDistancesOK = False
                    print("Fin3")
                    speaker_service.say(sentence)
                else:
                    print("Debut4")
                    print("Erreur, personne n'est detecte")
                    print("Fin4")
                    isWatchingSomeone = False
                
                print
                print("FIN DE LA VERIFICATION DES DISTANCES")
                print

                nothingChanged = True
                while(nothingChanged):
                    print("Boucle nothingChanged")
                    checkData(ClientMultiSocket, speaker_service,behavior_mng_service)
                    takePicture(photoCaptureProxy,ftp_client)
                    ClientMultiSocket.send("imageReady".encode())
                    ClientMultiSocket.recv(1024).decode()
                    time.sleep(refreshSpeed)
                    '''
                    #DEBUG
                    print
                    print("Boucle nothingChanged")
                    print("justArrived="+str(varJustArrived))
                    print("justLeft="+str(varJustArrived))
                    print("groupDistancesOK="+str(groupDistancesOK))            
                    #/!\ Source d'erreurs lors du debogage
                    try:        
                        print("rounded dist="+str(1 if round(value_service.getData("PeoplePerception/Person/"+str(peopleList[0])+"/Distance"),1)>1 else 0))
                    except:
                        print("rounded dist=undefined")
                    print("soloDistanceOK="+str(soloDistancesOK))
                    #/!\ Appel de la fonction
                    #print("checkGroupDistancesOK="+str(checkGroupDistancesOK(value_service.getData("PeoplePerception/VisiblePeopleList"), value_service)))
                    #print("groupDistancesOK="+str(groupDistancesOK))
                    '''

                    if(varJustArrived):
                        print("Case 1 : Nouvelle personne")
                        speaker_service.say("Coucou !")
                        ClientMultiSocket.send("someoneArrived".encode())
                        ClientMultiSocket.recv(1024)    
                        varJustArrived = False
                        nothingChanged = False


                    elif(varJustLeft):
                        print("Case 2 : Personne partie")
                        speaker_service.say("A plusse !")
                        if(len(peopleList) == 1):
                            isWatchingSomeone = False
                            speaker_service.say("Au revoir à tous !")
                            print("Il n'y a plus personne devant moi")
                            ClientMultiSocket.send("noOneLeft".encode())
                            ClientMultiSocket.recv(1024)  
                        varJustLeft = False
                        nothingChanged = False

                    #elif((1 if round(value_service.getData("PeoplePerception/Person/"+str(peopleList[0])+"/Distance"),1)>1 else 0) != soloDistancesOK and len(peopleList) == 1):
                    elif(len(peopleList) == 1):
                        #print("Pre-case 3 : Test si il y a quelqu'un devant")
                        try:
                            if((1 if round(value_service.getData("PeoplePerception/Person/"+str(peopleList[0])+"/Distance"),1)>1 else 0) != soloDistancesOK):
                                print("Case 3 : La personne devant s'est eloignee/rapprochee")
                                nothingChanged = False
                        except IndexError:
                            print("ERREUR D'INDEX")
                            time.sleep(5)
                            nothingChanged = True

                    elif(groupDistancesOK != checkGroupDistancesOK(value_service.getData("PeoplePerception/VisiblePeopleList"), value_service) and len(peopleList) > 1):
                        print("Case 4 : Changement dans les distances qui separent les membres du groupe")
                        speaker_service.say("Ah, je vois que vous avez bougé !")
                        nothingChanged = False

                    else:
                        print("Case 5 : nothingChanged")
                        nothingChanged = True
                '''
                if(tracker_service.isTargetLost()):
                    isWatchingSomeone = False
                    print("Personne sortie du champ de vision")
                    speaker_service.say("A bientôt !")
                '''
                print
                print("SORTIE Boucle isWatchingSomeone == TRUE")
                print
            
    except KeyboardInterrupt:
        print
        print ("Interrupted by user")
        print ("Stopping...")

    # Stop tracker.
    tracker_service.stopTracker()
    tracker_service.unregisterAllTargets()
    #motion_service.rest()  #Remet Pepper en position de veille

    print ("ALTracker stopped.")
    print ("############################################################")