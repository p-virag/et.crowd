#!/usr/bin/env micropython
#TODO 103 fel; 108 le    ellenorizni!!!!

try:
    #Imports used directories
    from ev3dev2.motor import *
    from ev3dev2.sensor import *
    from ev3dev2.sensor.lego import *
    #from ev3dev2.console import Console
    from ev3dev2.sound import *
    import time
    import sys
    import os

    #Defines motors globally
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

    #Defines sensors globally
    rightCS.mode = 'COL-REFLECT'
    leftCS.mode = 'COL-REFLECT'
    runCS.mode = 'COL-COLOR'
    kezdo_ido = open("ido.txt", "r+")
    t1=0.0
    t2=0.0

    #brake -> leallitsa-e a motorokat
    #block -> mehet-e kozben a kovetkezo parancs

#console.text_at("betöltöttem", reset_console=True)
except Exception as e: #error code
    print(e)


def returnGombok():
    """visszaadja a lenyomott gombok listáját"""
    return list(sys.stdin.readline().replace("\x1b[", "").rstrip())


# Changes modes and back to reset the GYRO
def gyroReset ():
    gyro.mode = 'GYRO-RATE'
    gyro.mode = 'GYRO-ANG'


def autoGyroReset ():
    """a futások elején használjuk, ha az operátorok elfelejtik resetelni a gyrot"""
    if abs(gyro.angle) >= 30:
        gyroReset()


#Function for straight moves with gyro used for directional accuracy
def gyroStraight (angle, speed, distance, sensitivity = 1, sensor = gyro, rightM = rightM, leftM = leftM, moveS = moveS, debug = False, motorBrake = True, motorReset = True):
    if motorReset: #Resets motors if True (Not used when changing speed, to take end distance from start of same directional move)
        rightM.reset(); leftM.reset()
    startGyro = 0 #0 -> abszolút, sensor.angle -> relatív
    while abs((rightM.position + leftM.position) / 2) < distance: #Works while the average of large motors gets to defined distance
        dif = angle - (sensor.angle - startGyro)
        if debug: print(dif)
        direction = dif * sensitivity
        if direction > 100: direction = 100
        if direction < -100: direction = -100
        moveS.on(-direction, speed)
    if motorBrake: #Turns brakes on if True
        moveS.off()
    else:
        #moveS.off(brake=False)
        pass


def linearDecel (direction, sensitivity, speedStart, speedEnd, distance, motorReset = True, motorBrake = True, debug = True):
    speedChange = speedStart - speedEnd #kiszámolja hogy mennyit kell lassítania a kezdő és végsebessége között
    startGyro = 0
    #a függvényváltozó alapján reseteli a motorokat és kiszámolja hogy mennyit kell előre haladnia
    if motorReset:
        moveT.reset()
        distanceCalc = distance
    else:
        distanceCalc = distance - abs((rightM.degrees + leftM.degrees) / 2)
    divider = distanceCalc / speedChange

    while abs((rightM.position + leftM.position) / 2) <= distance: #addig fut, amíg a két kerék átlaga nem haladja meg a megadott távolságot
        distanceCurrent = distanceCalc - abs((rightM.degrees + leftM.degrees) / 2) #meghatározza, hogy éppen mennyit haladt az indulás óta
        dif = direction - (gyro.angle - startGyro) #kiszámolja a gyro alapján, hogy mennyivel tér el a megadott foktól
        if debug: #ezt csak akkor használjuk, ha javítjuk
            print(dif)
            
        correction = dif * sensitivity #kiszámolja, hogy mennyit kell korrigálnia
        #ha a korrigálás túl nagy vagy túl kicsi, akkor visszaállítja a minimum/maximum értékre
        if correction > 100: correction = 100
        if correction < -100: correction = -100
        if debug:
            print(distanceCurrent, correction)
        #a motorokat a végsebességnél annyival gyorsabban hajtja meg, amennyire messze vannak a motorok attól a fordulatszámtól ameddig menni akarunk. A gyro sensor segítségével korrigál:
        moveS.on(-correction, ((distanceCurrent / divider) + speedEnd)) 
    
    #Leállítja a motorokat a függvényváltozótól függően:
    if motorBrake:
        moveS.off()

#Function for turning with gyro used for directional accuracy
def gyroTurn (angle, correction = 2, motor = moveT, gyrosensor = gyro, debug = False): #:)
    if debug: print("Start of turn")
    #abszolút fordulás
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
    """az elülső motort mozgatja"""
    medm.reset()
    medm.on_for_degrees(speed, degrees, block = block)


def topArm (speed, degrees = 90, block = True, medm = topM):
    """a felső motort mozgatja"""
    medm.reset()
    medm.on_for_degrees(speed, degrees, block = block)


def linePerpen (speed = 20, t = 3.5, sensitivity = 0.1, bright = 12):
    """the robot goes while it doesn't detect black (or white: depends on the 'bright' variables value) colour
    it get on the line perpendiculary"""
    while (rightCS.reflected_light_intensity or leftCS.reflected_light_intensity) >= bright: #moves the motors until one of the color sensors doesn't detect a line
        moveT.on(speed, speed)
    t1 = time.time() #save the actual time in a variable
    while t1 + t > time.time(): #it works as a timer: when the actual time is more than the sum of t (the given time) and t1 (the saved time) it stops
        #it runs the motors by the difference of reflected light aofinrianfewfdélk
        moveT.on(((leftCS.reflected_light_intensity - 40) * sensitivity), ((rightCS.reflected_light_intensity - 40) * sensitivity))
    moveT.off() #turns the motors off


def gyroToLine (angle = 0, speed = 40, sensitivity = 1, bright = 9, sensor = gyro, rightM = rightM, leftM = leftM, moveS = moveS, rightC = rightCS, leftC = leftCS, debug = False):
    """gyroval megy előre amíg fekete vonalat nem érzékel"""
    #világosban: 9, sötétben: 7
    sttarGyro = 0
    while (rightCS.reflected_light_intensity > bright) and (leftCS.reflected_light_intensity > bright): #amíg a színszenzorok feketét nem érzékelnek
        #ezek után ugyanúgy működik mint a gyros menés
        dif = angle - (sensor.angle - sttarGyro)
        direction = dif * sensitivity
        if direction > 100: direction = 100
        if direction < -100: direction = -100
        if debug: print(direction, speed)
        if debug: print(rightCS.reflected_light_intensity, leftCS.reflected_light_intensity)
        moveS.on(-direction, speed)


def ujido ():
    #törli és újra létrehozza a filet amiben az időt mentjük, azaz lenullázza
    kezdo_ido = open("ido.txt", "r+")
    os.remove("ido.txt")
    open("ido.txt", "w+")



def end ():
    #minden motort leállít (a kerekek guríthatóak). A futások végén használjuk
    moveT.off(brake=False)
    topM.off(brake=False)
    sideM.off(brake=False)


def run1 ():
    autoGyroReset() #hogyha még nincs, akkor reseteljük a gyrot
    sideArm(90, -240, block=False) #felemeli a kart -> lelöki az oldalsó pöcköt
    gyroStraight(-4, 50, 1000, 2) #egyenesen megy előre
    sideArm(90, 240, block=False) #visszaengedi a kart, hogy rátaláljon a rávezető a darura
    linearDecel(-4, 1.5, 40, 20, 600) #lassulva megy előre a daruig
    gyroTurn(2, 0.5) #ráfordul, hogy biztosan benyomja (és ne lengjen annyira)
    for i in range (10):
        #emelgeti a karját -> leereszti a darut
        sideArm(100, -140)
        sideArm(100, 140)
    #hazajön a bázisra:
    moveT.on_for_degrees(-20, -20, 140)
    moveT.on_for_degrees(-20, -30, 600)
    moveT.on_for_degrees(-40, -60, 1500)
    gyroStraight(-135, -100, 400, -1)
    gyroStraight(-165, -100, 200, -1)
    #leállítja a motorokat:
    end()


def run2 ():
    autoGyroReset() #hogyha még nincs, akkor reseteljük a gyrot
    #hintáig:
    gyroStraight(3, 80, 1600, 2, motorBrake=False) #feltoltve: fok = 1, szorzo = 2.5, lemerulve: sullyal: fok = 3, szorzo = 2.75, suly nelkul: fok = 3, szorzo = 2.5
    gyroStraight(-13, 80, 2500, 2, motorBrake=False, motorReset=False)
    gyroStraight(0, 40, 3400, 2, motorReset=False)
    #házig:
    gyroStraight(0, -40, 350, -1)
    gyroTurn(45)
    gyroStraight(45, 40, 940) #920
    gyroTurn(-45)
    gyroStraight(-45, 40, 400)
    gyroTurn(-90)
    #ház:
    gyroStraight(-90, -30, 560, -1) #
    time.sleep(0.5)
    gyroStraight(-90, 30, 100) #120
    sideArm(50, 435)
    gyroStraight(-90, 30, 420) #370
    #lift:
    gyroTurn(-54, 1) #-50
    gyroStraight(-54, -40, 800, -1)
    topArm(-60, 300)
    #hazajön:
    gyroTurn(-165, 1)
    gyroStraight(-165, 100, 1400)
    topArm(80, 400, block=False)
    gyroStraight(-190, 100, 3000) #-180
    #leállítja a motorokat:
    end()


def run3 ():
    autoGyroReset() #hogyha még nincs, akkor reseteljük a gyrot
    sideArm(40, -240, block = False) #felemeljük a kart -> a kockácskák nem potyognak le
    gyroStraight(0, 60, 1400) #előre megyünk
    linearDecel(0, 1, 60, 10, 450) #a fa előtt lassítunk
    time.sleep(0.5) #várunk egy kicsit
    sideArm(40, 250) #a kockákat rátesszük a fára
    time.sleep(0.5) #várunk egy kicsit
    #hátrajövünk és betesszük a kókuszt a körbe:
    gyroStraight(0, -10, 200, -0.5)
    gyroTurn(45)
    topArm(50, -600)
    #hazamegy a robot:
    gyroStraight(45, -20, 80, -1)
    moveT.on_for_degrees(20, 40, -680) #-600
    gyroStraight(-40, -90, 1700, -1)
    #leállítja a motorokat:
    end()


def run4 ():
    autoGyroReset() #hogyha még nincs, akkor reseteljük a gyrot
    #előre megyünk és letesszük a körbe a barna kockát:
    gyroStraight(-2, 50, 2750)
    gyroStraight(0, -30, 80)
    #a piros kockát is betesszük a körbe:
    gyroTurn(15, debug=True)
    gyroStraight(15, -50, 300, -1, debug=True)
    time.sleep(0.5)
    topArm(80, -360)
    #vonalat keresünk és merőlegesen állunk rá:
    linePerpen(sensitivity=0.2)
    print("gyro =", gyro.angle)
    #ha a gyro nem tér el 3-mal az eredetitől akkor reseteli (akkor pontosabb lesz, vagy nem rontja el mégjobban)
    if (gyro.angle >= -3) and (gyro.angle <= 3):
        moveT.off()
        #time.sleep(0.5)
        gyroReset()
        print("reseteltem!")
        time.sleep(0.5)
    #a hídhoz áll:
    gyroStraight(0, 15, 100)
    gyroTurn(-90)
    #felmegy a hídra:
    gyroStraight(-88, -90, 600, -2)
    gyroStraight(-88, -90, 1050, -3)
    gyroTurn(-90)    
    #ha kilógnánk az időből, akkor már nem emeli fel a kart:
    if t2 - t1 >= 145:
        moveT.off()
        ujido()
    #ha nem, akkor felemeli, és figyeli az időt, hogy mikor kell leengednie
    else:
        sideArm(40, 500)
        while True:
            kezdo_ido = open("ido.txt", "r+")
            t1 = float(kezdo_ido.readline()) #kezdő idő
            t2 = time.time() #aktuális idő
            if t2 - t1 >= 148: #gondolom 60 * 2.5 az 150 nem? szóval ekkor kell leengednie
                #leengedi a kart és nullázza az időt
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
        if runCS.value() == 3: #ha a színszenzor zöld színt érzékel:
            print("run1, green")
            topM.on(20, block = False) #elkezdi hajtani a felső motort, hogy könnyebb legyen a feltétet rárakni
            pressed = returnGombok() #gombnyomásra vár
            if runCS.value() == 3: #ellenőrzi a feltét színét
                if pressed == ['B']: #ha a lenyomott gomb 'B':
                    kezdo_ido = open("ido.txt", "r+") #megnyitja az időzítős fájlt
                    if len(kezdo_ido.readline()) == 0: #ha még nincs mentve az idő, akkor elmenti
                        kezdo_ido = open("ido.txt", "r+")
                        kezdo_ido.write(str(time.time()))
                    topM.off() #leállítja a fenti motort
                    time.sleep(0.5) #vár fél másodpercet, hogy az operátorok ne akadjanak bele
                    run1() #elindítja a megfelelő futást
                elif pressed == ['D']: #ha a lenyomott gomb 'D', akkor reseteli a gyrot
                    print("gyro")
                    gyroReset()
                manual() #manuálisan (színszenzor nélkül, gombkombinációkkal) is tudjuk indítani
            elif runCS.value() == 2: #ellenőrzi a feltét színét
                #ha a lenyomott gomb 'B', elmenti az időt, ha az még nincs elmentve, vár fél másodpercet és leállítja a fenti motort, mielőtt elindítja a futást
                if pressed == ['B']: 
                    kezdo_ido = open("ido.txt", "r+") 
                    if len(kezdo_ido.readline()) == 0:
                        kezdo_ido = open("ido.txt", "r+")
                        kezdo_ido.write(str(time.time()))
                    topM.off()
                    time.sleep(0.5)
                    run3()
                elif pressed == ['D']: #ha a lenyomott gomb 'D', akkor reseteli a gyrot
                    print("gyro")
                    gyroReset()
                manual() #manuálisan (színszenzor nélkül, gombkombinációkkal) is tudjuk indítani
        elif runCS.value() == 5: #ellenőrzi a feltét színét
            print("run2, red")
            topM.on(20, block = False) #elkezdi hajtani a felső motort, hogy könnyebb legyen a feltétet rárakni
            pressed = returnGombok() #gombnyomásra vár
            #ha a lenyomott gomb 'B', elmenti az időt, ha az még nincs elmentve, vár fél másodpercet és leállítja a fenti motort, mielőtt elindítja a futást
            if pressed == ['B']: 
                kezdo_ido = open("ido.txt", "r+")
                if len(kezdo_ido.readline()) == 0:
                    kezdo_ido = open("ido.txt", "r+")
                    kezdo_ido.write(str(time.time()))
                time.sleep(0.5)
                topM.off()
                run2()
            elif pressed == ['D']: #ha a lenyomott gomb 'D', akkor reseteli a gyrot
                print("gyro")
                gyroReset()
            manual() #manuálisan (színszenzor nélkül, gombkombinációkkal) is tudjuk indítani

        elif runCS.value() == 2: #ellenőrzi a feltét színét
            print("run3, blue")
            topM.on(20, block = False) #elkezdi hajtani a felső motort, hogy könnyebb legyen a feltétet rárakni
            pressed = returnGombok() #gombnyomásra vár
            #ha a lenyomott gomb 'B', elmenti az időt, ha az még nincs elmentve, vár fél másodpercet és leállítja a fenti motort, mielőtt elindítja a futást
            if pressed == ['B']: 
                kezdo_ido = open("ido.txt", "r+")
                if len(kezdo_ido.readline()) == 0:
                    kezdo_ido = open("ido.txt", "r+")
                    kezdo_ido.write(str(time.time()))
                time.sleep(0.5)
                topM.off()
                run3()
            elif pressed == ['D']: #ha a lenyomott gomb 'D', akkor reseteli a gyrot
                print("gyro")
                gyroReset()
            manual() #manuálisan (színszenzor nélkül, gombkombinációkkal) is tudjuk indítani

        elif runCS.value() == 4: #ellenőrzi a feltét színét
            print("run4, yellow")
            topM.on(20, block = False) #elkezdi hajtani a felső motort, hogy könnyebb legyen a feltétet rárakni
            pressed = returnGombok() #gombnyomásra vár
            #ha a lenyomott gomb 'B', elmenti az időt, ha az még nincs elmentve, vár fél másodpercet és leállítja a fenti motort, mielőtt elindítja a futást
            if pressed == ['B']: 
                kezdo_ido = open("ido.txt", "r+")
                if len(kezdo_ido.readline()) == 0:
                    kezdo_ido = open("ido.txt", "r+")
                    kezdo_ido.write(str(time.time()))
                time.sleep(0.5)
                topM.off()
                #print("elindultam: ",len(kezdo_ido.readline()))
                run4()
            elif pressed == ['D']: #ha a lenyomott gomb 'D', akkor reseteli a gyrot
                print("gyro")
                gyroReset()
            manual() #manuálisan (színszenzor nélkül, gombkombinációkkal) is tudjuk indítani
        

    except KeyboardInterrupt:
        #ha az 'A' gombot nyomjuk meg, leállítja a motorokat és visszalép a menübe
        end()
        print("MEGHAALT!!")
    
    except Exception as e: #error code
        print(e)


#aksitól függ: elso futas, fas cucc (?), hid szorzoja
        