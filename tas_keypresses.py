from pynput.keyboard import Key, Controller, KeyCode
from keyboard import wait
from time import sleep, time
import tarfile
from traceback import format_exc
from os.path import isfile
from math import gcd
#from collections import OrderedDict
#NOTE: This code relies on the Python 3.6+ implementation of guaranteed dict order.
#If this code is run on 3.5-, OrderedDict must be used instead.


keyboard = Controller()
debug = isfile("debug.txt")


def lcm(x, y):
    return x * y // gcd(x, y)


def fileParser(tasName):
    
    
    #keyMapDictNotOrdered = {}
    keyMapDict = {}    
    masterKeyList = []
    
    with open("mapping.txt") as fid:
        line = fid.readline().strip("\n").split(",")
        while line != ['']:
            #keyMapDictNotOrdered[line[0]] = line[1]
            keyMapDict[line[0]] = line[1]
            line = fid.readline().strip("\n").split(",")
   
    try:
        with tarfile.open(tasName) as tid:
            fid = tid.extractfile('inputs')        
        
        
        
            line = fid.readline().decode('utf-8').strip("\n").strip("|").split(":")
            i = 0
            
            
            while line != ['']:
                masterKeyList.append([])
                line[-1] = line[-1].strip("|.")
                line[0] = line[0].strip("K")
                for j,k in keyMapDict.items():
                    if j in line:
                        masterKeyList[i].append(k)
                    else:
                        masterKeyList[i].append(-1)
                i += 1
                line = fid.readline().decode('utf-8').strip("\n").strip("|").split(":")
            masterKeyList.append("EOF")
            
            fid.close()
            fid = tid.extractfile('config.ini')
            i = 0
            while i < 6:
                line = fid.readline()
                if i == 4:
                    den = int(line.decode('utf-8').strip("\n").split("=")[1])
                elif i == 5:
                    num = int(line.decode('utf-8').strip("\n").split("=")[1])
                i += 1
            fid.close()
    except:
        try:
            fid.close()
            tid.close()
        except:
            pass
        raise
    
    
    return keyMapDict, masterKeyList, num, den


def pressKeys(keypressList, lastKeypressList):
    debugCharPressessDelta = 0
    debugKeynamePressesDelta = 0
    debugKeycodePressesDelta = 0
    
    for i in range(len(keypressList)):
        if keypressList[i] != -1 and keypressList[i] != lastKeypressList[i]:
            if len(keypressList[i]) == 1 and keypressList[i].isalpha(): #Individual letters
                keyboard.press(keypressList[i])
                debugCharPressessDelta += 1
            elif keypressList[i] in dir(Key) or keypressList[i] == "shift_l": #Apparently shift_l isn't in dir(Key)
                keyboard.press(Key[keypressList[i]])
                debugKeynamePressesDelta += 1
            else:
                keyboard.press(KeyCode.from_vk(int(keypressList[i]))) #Numeric key codes
                debugKeycodePressesDelta += 1
    return debugCharPressessDelta, debugKeynamePressesDelta, debugKeycodePressesDelta


def releaseKeys(keyReleaseList):
    for i in range(len(keyReleaseList)):
        if keyReleaseList[i] != -1:
            if len(keyReleaseList[i]) == 1 and keyReleaseList[i].isalpha():
                keyboard.release(keyReleaseList[i])
            elif keyReleaseList[i] in dir(Key) or keyReleaseList[i] == "shift_l":
                keyboard.release(Key[keyReleaseList[i]])
            else:
                keyboard.release(KeyCode.from_vk(int(keyReleaseList[i])))
                
                
def keypressLoop(masterKeyList, carryTrigger, carryAmount, frameMicros, fps):
    debugStatsCount = 0
    debugActivePercentSum = 0
    debugNumCharPressess = 0
    debugNumKeynamePresses = 0
    debugNumKeycodePresses = 0
    debugMicrosLate = 0
    debugMaxMicrosLate = 0
    
    wakeUpTimer = 34000
    wakeDelta = 1000
    loopStart = time()*1000000
    
    carry = 0
    carryCount = 0
    cumulativeMicros = 0
    
    frameIndex = 0
    keypressList = masterKeyList[frameIndex]
    keyReleaseList = [0]*len(keypressList)
        

    
    while masterKeyList[frameIndex] != "EOF":
        # Get all the prep work done up here to reduce time in the input pressing section
        
        carryCount += 1
        if carryCount == carryTrigger:
            carryCount = 0
            carry = carryAmount
        else:
            carry = 0
        
        
        lastKeypressList = keypressList
        keypressList = masterKeyList[frameIndex]
        
        
        for i in range(len(keypressList)):
            if lastKeypressList[i] != -1 and keypressList[i] == -1:
                keyReleaseList[i] = lastKeypressList[i]
            else:
                keyReleaseList[i] = -1
            
            
        frameIndex += 1  
        cumulativeMicros += frameMicros + carry
        totalTime = frameMicros + carry
        
        
        inactiveTime, wakeUpTimer, wakeDelta = sleepLoop(loopStart, cumulativeMicros, wakeUpTimer, wakeDelta)
               


        if debug == 1:
            debugStatsCount += 1
            debugActivePercentSum += 100*((totalTime - inactiveTime)/totalTime)
            debugMicrosLate += time()*1000000 - loopStart - cumulativeMicros
            debugMaxMicrosLate = max(debugMaxMicrosLate, time()*1000000 - loopStart - cumulativeMicros)
            if debugStatsCount >= fps:
                debugStatsCount = 0
                
                print("{}% active".format(round(debugActivePercentSum/fps, 3)))
                debugActivePercentSum = 0
                
                print("{0} char presses\n{1} keyname presses\n{2} keycode presses"\
                      .format(debugNumCharPressess, debugNumKeynamePresses, debugNumKeycodePresses))
                debugNumCharPressess = 0
                debugNumKeynamePresses = 0
                debugNumKeycodePresses = 0
                
                print("{} average micros late".format(round(debugMicrosLate/fps, 3)))
                debugMicrosLate = 0
                
                print("{} max micros late".format(debugMaxMicrosLate))
                debugMaxMicrosLate = 0
                
                print("{} wake delta value".format(wakeDelta))
                
                print()
        
        
        
        
        
        
        
        # Only keypresses and releases should go here
        debugCharPressessDelta, debugKeynamePressesDelta, debugKeycodePressesDelta = \
            pressKeys(keypressList, lastKeypressList)
        releaseKeys(keyReleaseList)
        
        debugNumCharPressess += debugCharPressessDelta
        debugNumKeynamePresses += debugKeynamePressesDelta
        debugNumKeycodePresses += debugKeycodePressesDelta
        

def sleepLoop(loopStart, cumulativeMicros, wakeUpTimer, wakeDelta):
    sleepCheck = False
    inactiveTime = 0
    wakeDeltaDelta = 10
    
    while ((time()*1000000 - loopStart)) < cumulativeMicros:
        #Sleep loop

        diffTime = cumulativeMicros-(time()*1000000 - loopStart)
        if (diffTime - wakeUpTimer) > 0:
                       
            sleep((diffTime-wakeUpTimer)/1000000)
            inactiveTime = diffTime-wakeUpTimer
            

        if sleepCheck == False:
            #Only check once per loop and adjust the sleep time to maximize sleep without losing accuracy
            newDiffTime = cumulativeMicros-(time()*1000000 - loopStart)
            if (newDiffTime) < 0:
                wakeUpTimer += wakeDelta
            elif newDiffTime > wakeDelta:
                wakeUpTimer -= wakeDelta
            elif wakeDelta > wakeDeltaDelta:
                wakeDelta -= wakeDeltaDelta                
            if wakeUpTimer < wakeDelta:
                wakeUpTimer = wakeDelta
            sleepCheck = True
    return inactiveTime, wakeUpTimer, wakeDelta


def main():

    print("TAS Keypresses v1.0.1")
    print("By OceanBagel\n")
    
    print("This script requires two files in the same directory as the script: an ltm file and mapping.txt.")
    print("The ltm file is the TAS file to be run, with the .ltm extension. This file must be generated from libTAS.")
    print("mapping.txt contains lines of the form keycode,name where keycode is from libTAS (such as ff0d for enter) and name is the corresponding key name from pynput.")
    print("name can also be a character (such as x) or a keycode (such as 107).")
    print("Note: these don't need to refer to the same key. You can map a libTAS keyccode to a different key name if you want.")
    print("The key name is what will ultimately be pressed by the script when the corresponding keycode appears in the TAS.\n")
    
    tasName = input("Please enter the name of the TAS file:\n")
    
    if tasName[-4:].lower() != ".ltm":
        tasName += ".ltm"
    print()
    
    keyMapDict, masterKeyList, num, den = fileParser(tasName)
    
    fps = num/den



    # Correction factors. After carryTrigger number of frames, carryAmount microseconds are added to the timer.
    # This corrects for error due to using an integer number of microseconds, and avoids floating point rounding error.
    frameMicros = int(1000000/num)
    remainder = 1000000-(frameMicros*num)
    if remainder == 0:
        carryTrigger = 3
        carryAmount = 0
    else:
        carryTrigger = round(lcm(remainder, num)/remainder)
        carryAmount = round((remainder*carryTrigger)/num)
    
    #Multiply frameMicros and carryTrigger by den so frames are longer by a factor of den
    frameMicros *= den
    carryTrigger *= den
        
    
    if debug == 1:
        print("{0} fps, {1} micros, {2} carry trigger, {3} carry amount".format(fps, frameMicros, carryTrigger, carryAmount))
        print()
    
    print("There will be a 10 second countdown followed by the start of the TAS.")
    print("To prevent unintended operations, ensure an appropriate window has focus before continuing.")
    print("Press Enter to start the 10 second countdown.\n")
    
    wait("enter")
    print("Countdown has started.")
    for i in range(10):
        print(10-i)    
        sleep(1)
        
    print("\nBeginning keypresses...")
    
    #This function executes the keypresses and timing loop
    keypressLoop(masterKeyList, carryTrigger, carryAmount, frameMicros, fps)
    
    
    #Release the keys at the end, for when the tas file ends with a keypress
    for i in keyMapDict.values():
        if len(i) == 1 and i.isalpha():
            keyboard.release(i)
        elif i in dir(Key) or i == "shift_l":
            keyboard.release(Key[i])
        else:
            keyboard.release(KeyCode.from_vk(int(i)))
            
    print("\n\nTAS has ended. Press Esc to exit.")
    wait("esc")

try:
    
    main()
            
except:
    
    print("\n\n\nIf you're reading this, it means there was an error.\n\
Send angry messages to OceanBagel until he fixes it.\n\
When you do, copy and paste the following error message: \n\n")
    print(format_exc())  
    print("\nPress Esc to exit.")
    wait("esc")
    
