from pynput.keyboard import Key, Controller, KeyCode
from keyboard import wait
from time import sleep, time
import tarfile
from traceback import format_exc
from os.path import isfile
#from collections import OrderedDict
#NOTE: This code relies on the Python 3.6+ implementation of guaranteed dict order.
#If this code is run on 3.5-, OrderedDict must be used instead.


version = "v1.1.1"
keyboard = Controller()
debug = isfile("debug.txt")



def fileParser(tasName):
    
    
    #keyMapDictNotOrdered = {}
    keyMapDict = {}    
    masterKeyList = []
    masterFramerateList = []
    
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
                masterFramerateList.append([])
                line[-1] = line[-1].strip("|.")
                line[0] = line[0].strip("K")
                line = "|".join(line).split("|")                
                for j,k in keyMapDict.items():
                    if j in line:
                        masterKeyList[i].append(k)
                    else:
                        masterKeyList[i].append(-1)
                if len(line) > 1 and line[-2].startswith("T"):
                    masterFramerateList[i] = [int(line[-2].strip("T")), int(line[-1])] # Represents a framerate change, format [num, den]
                else:
                    masterFramerateList[i] = [0, 0] # Represents no framerate change

                    
                        
                        
                i += 1
                line = fid.readline().decode('utf-8').strip("\n").strip("|").split(":")
            masterKeyList.append("EOF")
            masterFramerateList.append("EOF")
            
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
    
    
    return keyMapDict, masterKeyList, num, den, masterFramerateList


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
                
                
def keypressLoop(masterKeyList, masterFramerateList, standardFrameMicros, fps):
    debugStatsCount = 0
    debugActivePercentSum = 0
    debugNumCharPressess = 0
    debugNumKeynamePresses = 0
    debugNumKeycodePresses = 0
    debugMicrosLate = 0
    debugMaxMicrosLate = 0
    
    wakeUpTimer = 34000
    wakeDelta = 100
    loopStart = time()*1000000
    minSleep = 1000 # Minimum microseconds per frame, under which sleep will not happen
    inactiveTime = 0

    cumulativeMicros = 0
    cumulativeCarry = 0
    
    frameIndex = 0
    keypressList = masterKeyList[frameIndex]
    keyReleaseList = [0]*len(keypressList)
        

    
    while masterKeyList[frameIndex] != "EOF":
        # Get all the prep work done up here to reduce time in the input pressing section
        
        
        lastKeypressList = keypressList
        keypressList = masterKeyList[frameIndex]
        
        
        for i in range(len(keypressList)):
            if lastKeypressList[i] != -1 and keypressList[i] == -1:
                keyReleaseList[i] = lastKeypressList[i]
            else:
                keyReleaseList[i] = -1
            
            
        
        
        # Calculate frame length for variable fps or take the standard frame length for fixed fps
        if masterFramerateList[frameIndex][1] == 0:
            frameMicros = standardFrameMicros
        else:
            frameMicros = 1000000 * masterFramerateList[frameIndex][1] / masterFramerateList[frameIndex][0]
        
        # Subtract off the non-integer portion and store it in frameCarry
        frameCarry = frameMicros - int(frameMicros)
        frameMicros -= frameCarry
        
        cumulativeCarry += frameCarry
        
        # Add integer portion of cumulativeCarry to frameMicros and subtract it off
        if cumulativeCarry >= 1:
            frameMicros += int(cumulativeCarry)
            cumulativeCarry -= int(cumulativeCarry)
        
        cumulativeMicros += frameMicros
        
        frameIndex += 1
        
        inactiveTime, wakeUpTimer, wakeDelta = sleepLoop(loopStart, cumulativeMicros, wakeUpTimer, wakeDelta, minSleep)


        if debug == 1:
            debugStatsCount += 1
            if frameMicros > 0:
                debugActivePercentSum += 100*((frameMicros - inactiveTime) / frameMicros)
            debugMicrosLate += time()*1000000 - loopStart - cumulativeMicros
            debugMaxMicrosLate = max(debugMaxMicrosLate, time()*1000000 - loopStart - cumulativeMicros)
            
            
            
            if debugStatsCount >= fps:
                 # Display the debug stats approximately once per second
                
                print("{}% active".format(round(debugActivePercentSum/debugStatsCount, 3)))
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
                
                print("{} wake timer value\n".format(wakeUpTimer))
        
                debugStatsCount = 0
        
        
        
        
        
        # Only keypresses and releases should go here
        debugCharPressessDelta, debugKeynamePressesDelta, debugKeycodePressesDelta = \
            pressKeys(keypressList, lastKeypressList)
        releaseKeys(keyReleaseList)
        
        debugNumCharPressess += debugCharPressessDelta
        debugNumKeynamePresses += debugKeynamePressesDelta
        debugNumKeycodePresses += debugKeycodePressesDelta
        

def sleepLoop(loopStart, cumulativeMicros, wakeUpTimer, wakeDelta, minSleep):
    sleepCheck = False
    inactiveTime = 0
    wakeDeltaDelta = 100
    minWakeUpTime = 1000
    
    while ((time()*1000000 - loopStart)) < cumulativeMicros:
        #Sleep loop

        diffTime = cumulativeMicros-(time()*1000000 - loopStart) # Amount of time to wait
        if (diffTime - wakeUpTimer) > minSleep: # Check for minimum sleep with extra time for waking up
                       
            sleep((diffTime-wakeUpTimer)/1000000)
            inactiveTime = diffTime-wakeUpTimer
            

        if sleepCheck == False:
            #Only check once per loop and adjust the sleep time to maximize sleep without losing accuracy
            newDiffTime = cumulativeMicros-(time()*1000000 - loopStart)
            if (newDiffTime) < -minWakeUpTime:
                wakeUpTimer += wakeDelta * 500
                wakeDelta += wakeDeltaDelta
            elif (newDiffTime) < 0:
                wakeUpTimer += wakeDelta
                wakeDelta += wakeDeltaDelta
            elif newDiffTime > wakeDelta:
                wakeUpTimer -= wakeDelta
                wakeDelta += wakeDeltaDelta
            elif wakeDelta > wakeDeltaDelta * 5:
                wakeDelta -= wakeDeltaDelta * 5     
            elif wakeDelta > wakeDeltaDelta:
                wakeDelta -= wakeDeltaDelta
            if wakeUpTimer < minWakeUpTime:
                wakeUpTimer = minWakeUpTime
            sleepCheck = True
    return inactiveTime, wakeUpTimer, wakeDelta


def main():

    print("TAS Keypresses " + version)
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
    
    keyMapDict, masterKeyList, num, den, masterFramerateList = fileParser(tasName)
    
    fps = num/den



    # Calculate the number of micros in a standard frame to use whenever fps isn't set for that frame    
    standardFrameMicros = 1000000 * den / num        
    
    if debug == 1:
        print("{0} fps, {1} micros".format(fps, standardFrameMicros))
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
    keypressLoop(masterKeyList, masterFramerateList, standardFrameMicros, fps)
    
    
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
    
