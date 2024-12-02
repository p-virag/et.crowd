#!/usr/bin/env micropython
#TODO 103 up; 108 down    check!!!!

try:
    # Imports used directories
    from ev3dev2.motor import *
    from ev3dev2.sensor import *
    from ev3dev2.sensor.lego import *
    #from ev3dev2.console import Console
    from ev3dev2.sound import *
    import time
    import sys
    import os

    # Defines motors and sensors globally
    moveS = MoveSteering(OUTPUT_A, OUTPUT_B)
    moveT = MoveTank(OUTPUT_A, OUTPUT_B)
    leftM = LargeMotor(OUTPUT_A)
    rightM = LargeMotor(OUTPUT_B)
    sideM = MediumMotor(OUTPUT_C)
    topM = MediumMotor(OUTPUT_D)
    gyro = GyroSensor(INPUT_3)
    rightCS = ColorSensor(INPUT_1)
    leftCS = ColorSensor(INPUT_2)
    runCS = ColorSensor(INPUT_4)
    #console = Console()
    #console.set_font(font="Lat15-TerminusBold32x16.psf.gz")

    # Sets up sensors and timer
    rightCS.mode = 'COL-REFLECT'
    leftCS.mode = 'COL-REFLECT'
    runCS.mode = 'COL-COLOR'
    kezdo_ido = open("ido.txt", "r+")
    t1=0.0
    t2=0.0

    # brake -> stop the motor?
    # block -> let the next command run?

#console.text_at("betöltöttem", reset_console=True)
except Exception as e: # error code
    print(e)


def returnGombok():
    """returns the list of pushed buttons."""
    return list(sys.stdin.readline().replace("\x1b[", "").rstrip())


# Changes modes and back to reset the GYRO
def gyroReset ():
    gyro.mode = 'GYRO-RATE'
    gyro.mode = 'GYRO-ANG'


def autoGyroReset ():
    """used at the beggining of a run if operators forgot to reset the gyro."""
    if abs(gyro.angle) >= 30:
        gyroReset()


# Function for straight moves with gyro used for directional accuracy
def gyroStraight (angle, speed, distance, sensitivity = 1, sensor = gyro, rightM = rightM, leftM = leftM, moveS = moveS, debug = False, motorBrake = True, motorReset = True):
    if motorReset: # Resets motors if True (Not used when changing speed, to take end distance from start of same directional move)
        rightM.reset(); leftM.reset()
    startGyro = 0 # 0 -> absolut, sensor.angle -> relative
    while abs((rightM.position + leftM.position) / 2) < distance: # Works while the average of large motors gets to defined distance
        dif = angle - (sensor.angle - startGyro)
        if debug: print(dif)
        direction = dif * sensitivity
        if direction > 100: direction = 100
        if direction < -100: direction = -100
        moveS.on(-direction, speed)
    if motorBrake: # Turns brakes on if True
        moveS.off()
    else:
        #moveS.off(brake=False)
        pass


def linearDecel (direction, sensitivity, speedStart, speedEnd, distance, motorReset = True, motorBrake = True, debug = True):
    speedChange = speedStart - speedEnd # Calculates the degree of deceleration
    startGyro = 0
    # Based on the function variable resets motors and calculates the distance
    if motorReset:
        moveT.reset()
        distanceCalc = distance
    else:
        distanceCalc = distance - abs((rightM.degrees + leftM.degrees) / 2)
    divider = distanceCalc / speedChange

    while abs((rightM.position + leftM.position) / 2) <= distance: # It runs until the avarage of the two wheels arent bigger than the given distance
        distanceCurrent = distanceCalc - abs((rightM.degrees + leftM.degrees) / 2) # Calculates the traveled distance from beggining
        dif = direction - (gyro.angle - startGyro) # Based on gyroscope value calculates the difference from given degree
        if debug: # Only used if malfunctioning
            print(dif)
            
        correction = dif * sensitivity # Calculates the needed amount of correction
        # If correction is too high or small resets to max/min value
        if correction > 100: correction = 100
        if correction < -100: correction = -100
        if debug:
            print(distanceCurrent, correction)
        moveS.on(-correction, ((distanceCurrent / divider) + speedEnd)) 
    
   if motorBrake:
        moveS.off()

# Function for turning with gyro used for directional accuracy
def gyroTurn (angle, correction = 2, motor = moveT, gyrosensor = gyro, debug = False): #:)
    if debug: print("Start of turn")
    # absolute turn
    startGyro = gyrosensor.angle
    if angle > 0 :
        while gyrosensor.angle != angle:
            dif = (angle - gyrosensor.angle) / correction
            if dif > 100: dif = 100
            if dif < -100: dif = -100
            motor.on(-dif, dif)
            if debug: print(gyrosensor.angle)
        
    else:
        while gyrosensor.angle != angle:
            dif = (angle - gyrosensor.angle) / correction
            if dif > 100: dif = 100
            if dif < -100: dif = -100
            motor.on(-dif, dif)
            if debug: print(gyrosensor.angle)
    motor.off()


def sideArm(speed, degrees, block = True, medm = sideM):
    """Moves the front engine"""
    medm.reset()
    medm.on_for_degrees(speed, degrees, block = block)


def topArm (speed, degrees = 90, block = True, medm = topM):
    """Moves the top engine"""
    medm.reset()
    medm.on_for_degrees(speed, degrees, block = block)


def linePerpen (speed = 20, t = 3.5, sensitivity = 0.1, bright = 12):
    """the robot goes while it doesn't detect black (or white: depends on the 'bright' variables value) colour
    it get on the line perpendiculary"""
    while (rightCS.reflected_light_intensity or leftCS.reflected_light_intensity) >= bright: # moves the motors until one of the color sensors doesn't detect a line
        moveT.on(speed, speed)
    t1 = time.time() # save the actual time in a variable
    while t1 + t > time.time(): # it works as a timer: when the actual time is more than the sum of t (the given time) and t1 (the saved time) it stops
        # it runs the motors by the difference of reflected light aofinrianfewfdélk
        moveT.on(((leftCS.reflected_light_intensity - 40) * sensitivity), ((rightCS.reflected_light_intensity - 40) * sensitivity))
    moveT.off() # turns the motors off


def gyroToLine (angle = 0, speed = 40, sensitivity = 1, bright = 9, sensor = gyro, rightM = rightM, leftM = leftM, moveS = moveS, rightC = rightCS, leftC = leftCS, debug = False):
    """goes forward (based on gyro values) until it detects a black line"""
    # in strong light: 9, in dark: 7
    sttarGyro = 0
    while (rightCS.reflected_light_intensity > bright) and (leftCS.reflected_light_intensity > bright):
        # from here it's just gyroStraight
        dif = angle - (sensor.angle - sttarGyro)
        direction = dif * sensitivity
        if direction > 100: direction = 100
        if direction < -100: direction = -100
        if debug: print(direction, speed)
        if debug: print(rightCS.reflected_light_intensity, leftCS.reflected_light_intensity)
        moveS.on(-direction, speed)


def ujido ():
    # deletes and creates the timer-file (aka resets to 0)
    kezdo_ido = open("ido.txt", "r+")
    os.remove("ido.txt")
    open("ido.txt", "w+")



def end ():
    # turnes off all engines (wheels can be rolled). used at the end of runs
    moveT.off(brake=False)
    topM.off(brake=False)
    sideM.off(brake=False)


def run1 ():
    autoGyroReset() # resets gyro if needed
    sideArm(90, -240, block=False) # lift up side arm (pushes off the side block)
    gyroStraight(-4, 50, 1000, 2) # goes forward
    sideArm(90, 240, block=False) # release the arm to allow the guide to find the crane
    linearDecel(-4, 1.5, 40, 20, 600) # slowing down to the crane
    gyroTurn(2, 0.5) # turns to make sure it pushes in (and doesn't swing so much)
    for i in range (10):
        # raises the arm -> lowers the crane
        sideArm(100, -140)
        sideArm(100, 140)
    # coming home to base
    moveT.on_for_degrees(-20, -20, 140)
    moveT.on_for_degrees(-20, -30, 600)
    moveT.on_for_degrees(-40, -60, 1500)
    gyroStraight(-135, -100, 400, -1)
    gyroStraight(-165, -100, 200, -1)
    # stops the engines
    end()


def run2 ():
    autoGyroReset()
    # to the swing:
    gyroStraight(3, 80, 1600, 2, motorBrake=False) # fully charged: fok = 1, szorzo = 2.5, halfway charged: with weight: fok = 3, szorzo = 2.75, without weight: fok = 3, szorzo = 2.5
    gyroStraight(-13, 80, 2500, 2, motorBrake=False, motorReset=False)
    gyroStraight(0, 40, 3400, 2, motorReset=False)
    # to the house:
    gyroStraight(0, -40, 350, -1)
    gyroTurn(45)
    gyroStraight(45, 40, 940) # 920
    gyroTurn(-45)
    gyroStraight(-45, 40, 400)
    gyroTurn(-90)
    # house:
    gyroStraight(-90, -30, 560, -1) #
    time.sleep(0.5)
    gyroStraight(-90, 30, 100) # 120
    sideArm(50, 435)
    gyroStraight(-90, 30, 420) # 370
    # the elevator:
    gyroTurn(-54, 1) # -50
    gyroStraight(-54, -40, 800, -1)
    topArm(-60, 300)
    # comes home:
    gyroTurn(-165, 1)
    gyroStraight(-165, 100, 1400)
    topArm(80, 400, block=False)
    gyroStraight(-190, 100, 3000) # -180
    # stops engines:
    end()


def run3 ():
    autoGyroReset()
    sideArm(40, -240, block = False) # lift arm -> blocks can't fall off
    gyroStraight(0, 60, 1400) # goes forward
    linearDecel(0, 1, 60, 10, 450) # slows down before the wall
    time.sleep(0.5) # wait
    sideArm(40, 250) # puts blocks on top of the tree
    time.sleep(0.5) # wait
    # comes backwards putting the coconut in the circle:
    gyroStraight(0, -10, 200, -0.5)
    gyroTurn(45)
    topArm(50, -600)
    # comes home:
    gyroStraight(45, -20, 80, -1)
    moveT.on_for_degrees(20, 40, -680) #-600
    gyroStraight(-40, -90, 1700, -1)
    # stops engines
    end()


def run4 ():
    autoGyroReset()
    # goes forward, puts the brown block in the circle:
    gyroStraight(-2, 50, 2750)
    gyroStraight(0, -30, 80)
    # puts the red block in the circle
    gyroTurn(15, debug=True)
    gyroStraight(15, -50, 300, -1, debug=True)
    time.sleep(0.5)
    topArm(80, -360)
    # looks for a line and stands perpendicular to it:
    linePerpen(sensitivity=0.2)
    print("gyro =", gyro.angle)
    # if gyro does not differ by 3 from the original it resets (it will be more accurate or not make it worse)
    if (gyro.angle >= -3) and (gyro.angle <= 3):
        moveT.off()
        #time.sleep(0.5)
        gyroReset()
        print("reseteltem!")
        time.sleep(0.5)
    # goes to the bridge:
    gyroStraight(0, 15, 100)
    gyroTurn(-90)
    # goes up to the bridge:
    gyroStraight(-88, -90, 600, -2)
    gyroStraight(-88, -90, 1050, -3)
    gyroTurn(-90)    
    # if time's up, it doesn't lift up the arm
    if t2 - t1 >= 145:
        moveT.off()
        ujido()
    # if not, it lifts arm and check time to lower arm before end of the game
    else:
        sideArm(40, 500)
        while True:
            kezdo_ido = open("ido.txt", "r+")
            t1 = float(kezdo_ido.readline()) # starting time
            t2 = time.time() # current time
            if t2 - t1 >= 148: # 60 * 2.5 = 150 so thats when it should be lowered
                # lowers arm and reset time
                sideArm(50, -500, block = False)
                topArmí(50, -500, block = False)
                os.remove("ido.txt")
                open("ido.txt", "w+")
        moveT.off()



def manual ():
    if pressed[0] == 'C':
        print("manual")
        if pressed == ['C', 'D']:
            kezdo_ido = open("ido.txt", "r+")
            if len(kezdo_ido.readline()) == 0:
                kezdo_ido = open("ido.txt", "r+")
                kezdo_ido.write(str(time.time()))
            time.sleep(0.5)
            run1()
        elif pressed == ['C', 'C']:
            kezdo_ido = open("ido.txt", "r+")
            if len(kezdo_ido.readline()) == 0:
                kezdo_ido = open("ido.txt", "r+")
                kezdo_ido.write(str(time.time()))
            time.sleep(0.5)
            run2()
        elif pressed == ['C', 'A']:
            kezdo_ido = open("ido.txt", "r+")
            if len(kezdo_ido.readline()) == 0:
                kezdo_ido = open("ido.txt", "r+")
                kezdo_ido.write(str(time.time()))
            time.sleep(0.5)
            run3()
        elif pressed == ['C', 'A', 'C']:
            kezdo_ido = open("ido.txt", "r+")
            if len(kezdo_ido.readline()) == 0:
                kezdo_ido = open("ido.txt", "r+")
                kezdo_ido.write(str(time.time()))
            time.sleep(0.5)
            run4()
        elif pressed == ['C', 'C', 'C']:
            print("gyro")
            gyroReset()
        elif pressed == ['C', 'B', 'B']:
            print("ido")
            ujido()


while True:
    try:
        if runCS.value() == 3: # if green is detected:
            print("run1, green")
            topM.on(20, block = False) # runs top engine to be easyer to attach module
            pressed = returnGombok() # waits for button press
            if runCS.value() == 3: # checks the colour of the module
                if pressed == ['B']: # if 'B' is pressed:
                    kezdo_ido = open("ido.txt", "r+") # open timer file
                    if len(kezdo_ido.readline()) == 0: # if no time is saved yet, it saves
                        kezdo_ido = open("ido.txt", "r+")
                        kezdo_ido.write(str(time.time()))
                    topM.off() # stops top engine
                    time.sleep(0.5) # waits (operators have time to take their hand back)
                    run1() # starts the correct run
                elif pressed == ['D']: # if 'D' is pressed resets gyro
                    print("gyro")
                    gyroReset()
                manual() # can be used without color sensor as well (manually, by pushing button-combinations)
            elif runCS.value() == 2: # checks the colour of the module
                # if 'B' is pressed: saves time if not yet saved, waits 0.5 second, stops top engine, starts run
                if pressed == ['B']: 
                    kezdo_ido = open("ido.txt", "r+") 
                    if len(kezdo_ido.readline()) == 0:
                        kezdo_ido = open("ido.txt", "r+")
                        kezdo_ido.write(str(time.time()))
                    topM.off()
                    time.sleep(0.5)
                    run3()
                elif pressed == ['D']: # if 'D' is pressed resets gyro
                    print("gyro")
                    gyroReset()
                manual() 
        elif runCS.value() == 5: # checks the colour of the module
            print("run2, red")
            topM.on(20, block = False) # runs top engine to be easyer to attach module
            pressed = returnGombok() # waits for button push
            # if 'B' is pressed: saves time if not yet saved, waits 0.5 second, stops top engine, starts run
            if pressed == ['B']: 
                kezdo_ido = open("ido.txt", "r+")
                if len(kezdo_ido.readline()) == 0:
                    kezdo_ido = open("ido.txt", "r+")
                    kezdo_ido.write(str(time.time()))
                time.sleep(0.5)
                topM.off()
                run2()
            elif pressed == ['D']: # if 'D' is pressed resets gyro
                print("gyro")
                gyroReset()
            manual()

        elif runCS.value() == 2: # checks the colour of the module
            print("run3, blue")
            topM.on(20, block = False) # runs top engine to be easyer to attach module
            pressed = returnGombok() # waits for button press
            # if 'B' is pressed: saves time if not yet saved, waits 0.5 second, stops top engine, starts run
            if pressed == ['B']: 
                kezdo_ido = open("ido.txt", "r+")
                if len(kezdo_ido.readline()) == 0:
                    kezdo_ido = open("ido.txt", "r+")
                    kezdo_ido.write(str(time.time()))
                time.sleep(0.5)
                topM.off()
                run3()
            elif pressed == ['D']: # if 'D' is pressed resets gyro
                print("gyro")
                gyroReset()
            manual()

        elif runCS.value() == 4: # checks the colour of the module
            print("run4, yellow")
            topM.on(20, block = False) # runs top engine to be easyer to attach module
            pressed = returnGombok() # waits for button press
            # if 'B' is pressed: saves time if not yet saved, waits 0.5 second, stops top engine, starts run
            if pressed == ['B']: 
                kezdo_ido = open("ido.txt", "r+")
                if len(kezdo_ido.readline()) == 0:
                    kezdo_ido = open("ido.txt", "r+")
                    kezdo_ido.write(str(time.time()))
                time.sleep(0.5)
                topM.off()
                #print("elindultam: ",len(kezdo_ido.readline()))
                run4()
            elif pressed == ['D']: # if 'D' is pressed resets gyro
                print("gyro")
                gyroReset()
            manual()
        

    except KeyboardInterrupt:
        # if 'A' is pressed stops engines and returns to main menu
        end()
        print("manually stopped")
    
    except Exception as e: # error code
        print(e)


# depends on battery charge: first run, tree, bridge multiplier
        
