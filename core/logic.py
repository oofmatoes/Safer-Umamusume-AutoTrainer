import time
from core.setUp import *
from core.betterOcr import *
from core.safeClick import *
import random
import math
import pyautogui
from PIL import ImageGrab

overlay = Overlay()
lastTurnText = ""
skipGoal = False
restUsedThisTurn = False

def getPixelColor(x, y):
    color = ImageGrab.grab(bbox=(x, y, x+1, y+1)).getpixel((0, 0))
    return color[:3]

def scanRectangle(rectangleName):
    topLeft, bottomRight = overlay.getRectangle(rectangleName)
    return getTextCords(topLeft, bottomRight)

def findBottomMost(topLeft, bottomRight, searchText):
    cords = getTextCords(topLeft, bottomRight)
    options = [
        (text, x, y) for text, (x, y) in cords.items() 
        if searchText in text
    ]
    return max(options, key=lambda option: option[2]) if options else None

def clickBottomMost(topLeft, bottomRight, searchText):
    result = findBottomMost(topLeft, bottomRight, searchText)
    if result:
        text, x, y = result
        return safeClick(x, y, text)
    return False

def clickRace(topLeft, bottomRight):
    if findAndClick(topLeft, bottomRight, "Race"):
        time.sleep(1.5)
        return clickBottomMost(topLeft, bottomRight, "Race")
    return False

def reset():
    topLeft, bottomRight = overlay.getRectangle("SAFE_AREA_REGION")
    randomX = random.randint(int(topLeft[0]), int(bottomRight[0]))
    randomY = random.randint(int(topLeft[1]), int(bottomRight[1]))
    safeClick(randomX, randomY, "safe_area")

def getTurnText(turnCords):
    return " ".join(turnCords.keys()) if turnCords else ""

def waitForBack():
    while True:
        mainCords = scanRectangle("MAIN_BUTTONS_REGION")
        if any("Back" in text for text in mainCords.keys()):
            break

def mainLoop():
    global lastTurnText, skipGoal, restUsedThisTurn
    
    while True:
        turnCords = scanRectangle("TURN_REGION")
        topLeft, bottomRight = overlay.getRectangle("MAIN_BUTTONS_REGION")
        mainCords = scanRectangle("MAIN_BUTTONS_REGION")
        
        currentTurnText = getTurnText(turnCords)

        if currentTurnText != lastTurnText and currentTurnText != "":
            lastTurnText = currentTurnText
            skipGoal = False
            restUsedThisTurn = False

        #low energy? Rest
        if overlay.getEnergyPercent() < 50 and not restUsedThisTurn:
            if findAndClick(topLeft, bottomRight, "Rest"):
                restUsedThisTurn = True
                continue

        infPos = overlay.savedPositions["infirmary"]
        infColor = getPixelColor(int(infPos.x), int(infPos.y))
        r, g, b = infColor
        
        #Sick? visit inf
        if abs(r - 160) <= 30 and abs(g - 110) <= 25 and abs(b - 246) <= 40:
            if safeClick(int(infPos.x), int(infPos.y), "infirmary"):
                continue

        #Bad mood and energy not full?
        moodCords = scanRectangle("MOOD_REGION")
        if any(mood in text for text in moodCords.keys() for mood in ["NORMAL", "BAD", "AWFUL"]) and overlay.getEnergyPercent() < 80:
            if findAndClick(topLeft, bottomRight, "Recreation"):
                continue

        criteriaCords = scanRectangle("CRITERIA_REGION")

        #Goal yet to be met
        if any("Criteria" in text or "Progress" in text for text in criteriaCords.keys()) and not skipGoal:
            if clickBottomMost(topLeft, bottomRight, "Race"):
                waitForBack()
                mainCords = scanRectangle("MAIN_BUTTONS_REGION")
                if any("Recommended!" in text for text in mainCords.keys()):
                    if clickBottomMost(topLeft, bottomRight, "Race"):
                        continue
                else:
                    skipGoal = True
                    if findAndClick(topLeft, bottomRight, "Back"):
                        continue

        #Time to race
        if any("Race" in text for text in turnCords.keys()):
            if findAndClick(topLeft, bottomRight, "Race!"):
                continue
            if clickRace(topLeft, bottomRight):
                continue

        #In Race menu
        if any(keyword in text for text in mainCords.keys() for keyword in ["Pace", "Late", "End", "Front"]):
            if findAndClick(topLeft, bottomRight, "Race!"):
                continue

        if any("Enter" in text for text in mainCords.keys()):
            if clickRace(topLeft, bottomRight):
                continue

        if any("View" in text for text in mainCords.keys()) and any("Results" in text for text in mainCords.keys()):
            if findAndClick(topLeft, bottomRight, "Results"):
                continue
            
        if any("Next" in text for text in mainCords.keys()):
            if findAndClick(topLeft, bottomRight, "Next"):
                continue
        print("aaa")
        if any("Training" in text for text in mainCords.keys()):
            if findAndClick(topLeft, bottomRight, "Training"):
                continue
            
        if any("Cancel" in text for text in mainCords.keys()):
            if clickBottomMost(topLeft, bottomRight, "Race"):
                waitForBack()
                if clickBottomMost(topLeft, bottomRight, "Race"):
                    continue

        if any("GO!" in text for text in mainCords.keys()):
            if findAndClick(topLeft, bottomRight, "GO!"):
                continue

        statusCords = scanRectangle("STATUS_REGION")
        if any("Training" in text for text in statusCords.keys()):
            safeTopLeft, safeBottomRight = overlay.getRectangle("SAFE_AREA_REGION")
            randomX = random.randint(int(safeTopLeft[0]), int(safeBottomRight[0]))
            randomY = random.randint(int(safeTopLeft[1]), int(safeBottomRight[1]))
            moveCursor(randomX, randomY)
            pyautogui.mouseDown()
            
            supportTopLeft, supportBottomRight = overlay.getRectangle("SUPPORT_CARD_ICON_REGION")
            trainingOptions = ["Speed", "Stamina", "Power", "Wit"]
            buttonFriendCounts = {}
            
            for option in trainingOptions:
                result = findBottomMost(topLeft, bottomRight, option)
                if result:
                    _, x, y = result
                    moveCursor(int(x), int(y))
                    time.sleep(1)
                    friendCount = friendCheck(supportTopLeft, supportBottomRight, option)
                    buttonFriendCounts[option] = friendCount
                else:
                    buttonFriendCounts[option] = 0
            
            currentEnergy = overlay.getEnergyPercent()
            
            if currentEnergy > 90:
                validOptions = {option: count for option, count in buttonFriendCounts.items() if option != "Wit"}
            else:
                validOptions = buttonFriendCounts
            
            if not validOptions:
                bestButton = "Wit"
            else:
                maxFriends = max(validOptions.values())
                tiedOptions = [option for option, count in validOptions.items() if count == maxFriends]
                
                if "Speed" in tiedOptions:
                    bestButton = "Speed"
                else:
                    bestButton = tiedOptions[0]
                
                if maxFriends == 0:
                    bestButton = "Wit"
            
            bestResult = findBottomMost(topLeft, bottomRight, bestButton)
            if bestResult:
                _, x, y = bestResult
                moveCursor(int(x), int(y))
                time.sleep(1)
                pyautogui.mouseUp()
                pyautogui.click()
                continue
            else:
                pyautogui.mouseUp()
        
        playAreaTopLeft, playAreaBottomRight = overlay.getRectangle("PLAY_AREA_REGION")
        if findAndClickImage(playAreaTopLeft, playAreaBottomRight, "assets\\icons\\event_choice_1.png"):
            continue
        
        if not turnCords:
            reset()
        
        time.sleep(1)