# coding: utf-8
import os, sys
import time
import asyncio
import COVID19Py
import cozmo
import random
from cozmo.util import degrees, distance_mm, speed_mmps


#   setup things
#__________________________________________________
# May cause an error, comment if needed
covid19 = COVID19Py.COVID19()
covid19 = COVID19Py.COVID19(data_source="jhu")
print("[COZMO] Covid API Checked")

_clock_font = None


try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit("Cannot import from PIL. Do `pip3 install --user Pillow` to install")

try:
    _clock_font = ImageFont.truetype("calibri.ttf", 20)
except IOError:
    try:
        _clock_font = ImageFont.truetype("/Library/Fonts/Calibri.ttf", 20)
    except IOError:
        pass


SHOW_ANALOG_CLOCK = False
ThereIsSomeone = False
freePlayMode = False
lowbatvoltage = 3.7


#__________________________________________________
#                    Server
#__________________________________________________
#Cette fonction est appelée pour préparer cozmo à recevoir un dialogue
#quand le serveur envoie "stop" on quitte cette boucle
def treatDialog(ClientMultiSocket,robot):
    global ThereIsSomeone

    while True:
        ClientMultiSocket.send("getData".encode())
        res = ClientMultiSocket.recv(1024).decode()
        ClientMultiSocket.send("keepIt".encode())

        if res!="noData":

                if(res=="behavior"):
                    res = ClientMultiSocket.recv(1024).decode()
                    ClientMultiSocket.send("keepIt".encode())
                    ClientMultiSocket.recv(1024)

                    if(res == "playAngryAnim"):
                        print("[COZMO-ANIM] Playing Angry anim")
                        robot.play_anim_trigger(cozmo.anim.Triggers.CodeLabFrustrated).wait_for_completed()    
                        #robot.say_text("Il a raison, écartez vous ", False, use_cozmo_voice=True).wait_for_completed() 
                    
                    if(res == "playHappyAnim"):
                        print("[COZMO-ANIM] Playing Happy anim")
                        robot.play_anim_trigger(cozmo.anim.Triggers.CodeLabHappy).wait_for_completed()    
                        #robot.say_text("Merci de respecter les distances ", False, use_cozmo_voice=True).wait_for_completed() 
                    
                    if(res == "maskOn"):
                        print("[COZMO-ANIM] Playing Happy anim because of mask")
                        a = random.randint(0, 2)
                        if(a == 1): 
                            robot.play_anim_trigger(cozmo.anim.Triggers.CodeLabPartyTime)
                        if(a == 2): 
                            robot.play_anim_trigger(cozmo.anim.Triggers.CodeLabHappy)
                        if(a == 0): 
                            robot.play_anim_trigger(cozmo.anim.Triggers.CodeLabVictory)
                        print("[COZMO] Played Mask animation")

                    if(res == "maskOff"):
                        print("[COZMO-ANIM] Playing Happy anim because no mask")
                        a = random.randint(0, 2)
                        if(a == 1): 
                            robot.play_anim_trigger(cozmo.anim.Triggers.CodeLabFireTruck)
                        if(a == 2): 
                            robot.play_anim_trigger(cozmo.anim.Triggers.CodeLabScaredCozmo)
                        if(a == 0): 
                            robot.play_anim_trigger(cozmo.anim.Triggers.CodeLabLose)
                        print("[COZMO] Played whithout Mask animation")


                if(res=="msg"):
                    res = ClientMultiSocket.recv(1024).decode()
                    ClientMultiSocket.send("keepIt".encode())
                    ClientMultiSocket.recv(1024).decode()
                    robot.say_text(res, False, use_cozmo_voice=True).wait_for_completed() 
                    print(res)

                   
                if(res=="stop"):
                    ClientMultiSocket.recv(1024).decode()
                    break        

        else:
            ClientMultiSocket.recv(1024).decode()
        

#Cette fonction est appelée à chaque début de boucle, elle reçoit une information du serveur . 
#Si elle est différente de noData on décide de ce qu'on fait d'elle
def checkData(ClientMultiSocket,robot):
    #print("[cozmo] started checking data")

    global ThereIsSomeone
    ClientMultiSocket.send("getData".encode())
    res = ClientMultiSocket.recv(1024).decode()
    #print("[cozmo] received nodata ? " + str(res))
    #checkBattery(robot)

    if(res!="noData"):
        ClientMultiSocket.send("keepIt".encode())
        ClientMultiSocket.recv(1024).decode()
        print("[cozmo] received : "+ str(res))

        if(ThereIsSomeone):
            print("[COZMO] There is someone - Received : " + res)

            if(res=="dialog"):
                print("[COZMO] Let's dialog")
                stopFreePlay(robot)
                treatDialog(ClientMultiSocket,robot)
                print("[COZMO] Finished dialog, restarting freeplay...")
                startFreePlay(robot)

            if(res == "goToSleep"):
                print("[COZMO] People left : Let's play and wait alone !")
                ThereIsSomeone = False
                startFreePlay(robot)
        
            if(res == "covidInfo"):
                print("[COZMO] Received COVIDINFO")
                stopFreePlay(robot)
                cozmoPresentation(robot)
                startFreePlay(robot)

        if(not ThereIsSomeone and res == "someoneArrived"):
            print("[cozmo][1] someone arrived, preparing to meet")
            ThereIsSomeone = True  
            stopFreePlay(robot)
            prepareToMeet(robot)
            print("[cozmo][2] someone arrived, restarting freeplay")
            startFreePlay(robot)

    else:
        ClientMultiSocket.send("keepIt".encode())
        res=ClientMultiSocket.recv(1024).decode()

#__________________________________________________
#              Cozmo functions
#__________________________________________________
def make_text_image(text_to_draw, x, y, font=None):
    '''Make a PIL.Image with the given text printed on it

    Args:
        text_to_draw (string): the text to draw to the image
        x (int): x pixel location
        y (int): y pixel location
        font (PIL.ImageFont): the font to use

    Returns:
        :class:(`PIL.Image.Image`): a PIL image with the text drawn on it
    '''

    # make a blank image for the text, initialized to opaque black
    text_image = Image.new('RGBA', cozmo.oled_face.dimensions(), (0, 0, 0, 255))

    # get a drawing context
    dc = ImageDraw.Draw(text_image)

    # draw the text
    dc.text((x, y), text_to_draw, fill=(255, 255, 255, 255), font=font)

    return text_image

#__________________________________________________
def get_in_position(robot: cozmo.robot.Robot):
    '''If necessary, Move Cozmo's Head and Lift to make it easy to see Cozmo's face'''
    if (robot.lift_height.distance_mm > 45) or (robot.head_angle.degrees < 40):
        with robot.perform_off_charger():
            lift_action = robot.set_lift_height(0.0, in_parallel=True)
            head_action = robot.set_head_angle(cozmo.robot.MAX_HEAD_ANGLE,
                                               in_parallel=True)
            lift_action.wait_for_completed()
            head_action.wait_for_completed()


#__________________________________________________
def startFreePlay(robot: cozmo.robot.Robot):
    global freePlayMode
    if(not freePlayMode):
        freePlayMode = True
        #robot.start_freeplay_behaviors()
        print("[COZMO] Starting freePlay")
        return True
    return False

#__________________________________________________
def checkBattery(robot: cozmo.robot.Robot):
    global lowbatvoltage
    if(robot.battery_voltage <= lowbatvoltage):
        print("[COZMO] is tired, battery is : " + str(robot.battery_voltage))
        goToSleep(robot)
        return True
    return False

#__________________________________________________
def stopFreePlay(robot: cozmo.robot.Robot):
    global freePlayMode
    if(freePlayMode):
        freePlayMode = False
        robot.stop_freeplay_behaviors()
        print("[COZMO] Ending freePlay")
        return True
    return False

#__________________________________________________
def initializeCozmo(robot: cozmo.robot.Robot):
    if robot.is_on_charger and not checkBattery(robot):
        #drive off the charger
        robot.drive_off_charger_contacts().wait_for_completed()
        robot.drive_straight(distance_mm(100), speed_mmps(50)).wait_for_completed()
    robot.set_robot_volume(0.5)
    startFreePlay(robot)
    return True

#__________________________________________________
def prepareToMeet(robot: cozmo.robot.Robot):
    # Move lift down and tilt the head up
    robot.move_lift(-3)
    robot.set_head_angle(cozmo.robot.MAX_HEAD_ANGLE).wait_for_completed()

#__________________________________________________
#   INTRODUCE COVID NEWS
#__________________________________________________
#def displayMask(robot: cozmo.robot.Robot):


def introduce_covid_news(robot: cozmo.robot.Robot):

    current_directory = os.path.dirname(os.path.realpath(__file__))
    mask_png = os.path.join(current_directory,  "pic", "mask.png")
    stonks_png = os.path.join(current_directory, "pic", "stonks.png")

    # load some images and convert them for display cozmo's face
    image_settings = [(mask_png, Image.BICUBIC),
                      (stonks_png, Image.NEAREST)]
    face_images = []
    for image_name, resampling_mode in image_settings:
        image = Image.open(image_name)

        # resize to fit on Cozmo's face screen
        resized_image = image.resize(cozmo.oled_face.dimensions(), resampling_mode)

        # convert the image to the format used by the oled screen
        face_image = cozmo.oled_face.convert_image_to_screen_data(resized_image,
                                                                 invert_image=True)
        face_images.append(face_image)

    # display each image on Cozmo's face for duration_s seconds (Note: this
    # is clamped at 30 seconds max within the engine to prevent burn-in)
    # repeat this num_loops times

    num_loops = 1
    duration_s = 2.0

    print("Press CTRL-C to quit (or wait %s seconds to complete)" % int(num_loops*duration_s) )
    s1 = "OK, je vais chercher ça sur internet, et je change de voix..."
    s = "Bonsoir, je vais vous donner les news"
    robot.say_text(s1, False, voice_pitch=-1, duration_scalar=0.4, use_cozmo_voice=True).wait_for_completed()    
    a4 = robot.play_anim_trigger(cozmo.anim.Triggers.CodeLabFrustrated).wait_for_completed()        

    a1 = robot.say_text(s, False, voice_pitch=-1, duration_scalar=0.4, use_cozmo_voice=False)
    #a2 = robot.display_oled_face_image(face_images[0], duration_s * 1000.0)
    a3 = robot.display_oled_face_image(face_images[1], duration_s * 1000.0)
    time.sleep(duration_s)

    a1.wait_for_completed()    
    #a2.wait_for_completed()    
    a3.wait_for_completed()    

#__________________________________________________
def statistics():
    #latestWorld = covid19.getLatest()
    #print(latestWorld["confirmed"])

    france = covid19.getLocationByCountryCode("FR", timelines=True)
    tab = []

    for k, v in france[-1]['timelines']['confirmed']['timeline'].items():
        tab.append(v)

    pastWeekCase = tab[-7]
    todayCase = tab[-1]

    percentage = 100 * (todayCase - pastWeekCase) / pastWeekCase
    augmentation = todayCase - pastWeekCase
    print(percentage)
    return [str(pastWeekCase), str(todayCase), str(augmentation) ,str(round(percentage,2))+'%']

#__________________________________________________
def sentence(i):
    switcher={
            0:'Le nombre de cas de la semaine dernière était de ',
            1:'Le nombre de cas aujourdhui est ',
            2:"Le nombre de nouveaux cas est donc de ",
            3:'Ce qui équivaut à un pourcentage de '
            }
    return switcher.get(i,"Invalid request")

#__________________________________________________
def actions(robot: cozmo.robot.Robot, cpt,value):
    #SAY TEXT
    s = sentence(cpt) + value
    #robot.say_text(s).wait_for_completed()
    a1 = robot.say_text(s, False, voice_pitch=-1, duration_scalar=0.4, use_cozmo_voice=False)

    #PRINT TEXT
    image = make_text_image(value,8, 6, _clock_font)
    print("----------------- > Image created")
    oled_face_data = cozmo.oled_face.convert_image_to_screen_data(image)
    print("----------------- > oled face data created")
    # display for 10 second
    a2 = robot.display_oled_face_image(oled_face_data, 10000.0)
    a1.wait_for_completed()    
    a2.wait_for_completed()    
    print("----------------- > Image displayed")
    time.sleep(1)

#__________________________________________________
def cozmoPresentation(robot: cozmo.robot.Robot):

    get_in_position(robot)
    print("----------------- > Starting presentation")

    introduce_covid_news(robot)

    stat = statistics()
    cpt = 0

    print(stat)

    for i in stat:
        print(i)
        actions(robot, cpt, i)
        cpt+=1

    s1 = "Voilà, allez vous faire vacciner maintenant s'il vous plait"
    robot.say_text(s1, False, use_cozmo_voice=True).wait_for_completed()    

    print("----------------- > Finished presentation")


#__________________________________________________
#   FACE FOLLOWER
#__________________________________________________

def follow_faces(robot: cozmo.robot.Robot):
    print("[COZMO] Starting Face to Follow")

    if robot.is_on_charger:
        # drive off the charger
        robot.drive_off_charger_contacts().wait_for_completed()
        robot.drive_straight(distance_mm(100), speed_mmps(50)).wait_for_completed()

    '''The core of the follow_faces program'''

    # Move lift down and tilt the head up
    robot.move_lift(-3)
    robot.set_head_angle(cozmo.robot.MAX_HEAD_ANGLE).wait_for_completed()

    face_to_follow = None
    cpt = 0

    while cpt < 3:
        
        #print("Press CTRL-C to quit")
        print("[COZMO] Searching for Face to Follow")
        turn_action = None
        if face_to_follow:
            # start turning towards the face
            turn_action = robot.turn_towards_face(face_to_follow)
            robot.set_all_backpack_lights(cozmo.lights.blue_light)


        if not (face_to_follow and face_to_follow.is_visible):
            robot.set_backpack_lights_off()
            # find a visible face, timeout if nothing found after a short while
            try:
                face_to_follow = robot.world.wait_for_observed_face(timeout=2)
            except asyncio.TimeoutError:
                print("Didn't find a face - exiting!")
                return

        if turn_action:
            # Complete the turn action if one was in progress
            turn_action.wait_for_completed()

        time.sleep(.1)
        cpt+=1

def drive_to_charger(robot):
    '''The core of the drive_to_charger program'''

    # If the robot was on the charger, drive them forward and clear of the charger
    if robot.is_on_charger:
        # drive off the charger
        robot.drive_off_charger_contacts().wait_for_completed()
        robot.drive_straight(distance_mm(100), speed_mmps(50)).wait_for_completed()
        # Start moving the lift down
        robot.move_lift(-3)
        # turn around to look at the charger
        robot.turn_in_place(degrees(180)).wait_for_completed()
        # Tilt the head to be level
        robot.set_head_angle(degrees(0)).wait_for_completed()
        # wait half a second to ensure Cozmo has seen the charger
        time.sleep(0.5)
        # drive backwards away from the charger
        robot.drive_straight(distance_mm(-60), speed_mmps(50)).wait_for_completed()

    # try to find the charger
    charger = None

    # see if Cozmo already knows where the charger is
    if robot.world.charger:
        if robot.world.charger.pose.is_comparable(robot.pose):
            print("Cozmo already knows where the charger is!")
            charger = robot.world.charger
        else:
            # Cozmo knows about the charger, but the pose is not based on the
            # same origin as the robot (e.g. the robot was moved since seeing
            # the charger) so try to look for the charger first
            pass

    if not charger:
        # Tell Cozmo to look around for the charger
        look_around = robot.start_behavior(cozmo.behavior.BehaviorTypes.LookAroundInPlace)
        try:
            charger = robot.world.wait_for_observed_charger(timeout=30)
            print("Found charger: %s" % charger)
        except asyncio.TimeoutError:
            print("Didn't see the charger")
        finally:
            # whether we find it or not, we want to stop the behavior
            look_around.stop()

    if charger:
        # Attempt to drive near to the charger, and then stop.
        action = robot.go_to_object(charger, distance_mm(65.0))
        action.wait_for_completed()
        robot.turn_in_place(degrees(180)).wait_for_completed()
        robot.drive_straight(distance_mm(-150), speed_mmps(50)).wait_for_completed()
        print("Completed action: result = %s" % action)
        print("Done.")

def goToSleep(robot: cozmo.robot.Robot):
    print("[COZMO] Going to sleep")
    drive_to_charger(robot)
