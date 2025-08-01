import pyautogui
import time
import random
import math
from datetime import datetime

pyautogui.MINIMUM_DURATION = 0
pyautogui.PAUSE = 0

lastClickedButtons = {}

class clickInfo:
    def __init__(self, position, timestamp, buttonText):
        self.position = position
        self.timestamp = timestamp
        self.buttonText = buttonText

def canClickButton(buttonText, position):
    if buttonText not in lastClickedButtons:
        return True
    
    lastClick = lastClickedButtons[buttonText]
    timeDiff = (datetime.now() - lastClick.timestamp).total_seconds()
    
    if timeDiff < 2:
        return False
    
    distance = math.sqrt((position[0] - lastClick.position[0])**2 + (position[1] - lastClick.position[1])**2)
    return distance >= 10 or timeDiff >= 0.5

def moveCursor(toX, toY):
    randomOffsetX = random.randint(-16, 16)
    randomOffsetY = random.randint(-16, 16)
    toX += randomOffsetX
    toY += randomOffsetY
    
    currentX, currentY = pyautogui.position()
    startX = float(currentX)
    startY = float(currentY)
    
    dist = math.sqrt((toX - startX)**2 + (toY - startY)**2)
    totalTime = max(0.25, min(1.0, dist / 2000.0))
    steps = max(1, int(totalTime * 60))
    
    jitterX = 0.0
    jitterY = 0.0
    jitterCount = 0
    
    for i in range(1, steps + 1):
        p = i / steps
        shake = 1.0 - p * p
        
        if dist > 300:
            accelP = 1 - (1 - p) ** 3
            nowX = startX + (toX - startX) * accelP
            nowY = startY + (toY - startY) * accelP
        else:
            if p < 0.7:
                adjustedP = p / 0.7
                nowX = startX + (toX - startX) * adjustedP
                nowY = startY + (toY - startY) * adjustedP
            else:
                tVal = (p - 0.7) / 0.3
                overshootP = 1.0 + 0.1 * math.sin(tVal * math.pi)
                nowX = startX + (toX - startX) * overshootP
                nowY = startY + (toY - startY) * overshootP
        
        if jitterCount <= 0:
            jitterCount = random.randint(3, 8)
            jitterX = (random.random() - 0.5) * 8.0
            jitterY = (random.random() - 0.5) * 8.0
        
        jitterCount -= 1
        
        finalX = int(nowX + jitterX * shake)
        finalY = int(nowY + jitterY * shake)
        pyautogui.moveTo(finalX, finalY)
        time.sleep(0.015 + random.random() * 0.006)
    
    pyautogui.moveTo(toX, toY)

def click():
    pyautogui.mouseDown()
    time.sleep(0.166 + random.random() * 0.237)
    pyautogui.mouseUp()

def safeClick(x, y, buttonText=""):
    if buttonText and not canClickButton(buttonText, (x, y)):
        return False
    
    moveCursor(int(x), int(y))
    
    if buttonText:
        lastClickedButtons[buttonText] = clickInfo(
            position=(x, y),
            timestamp=datetime.now(),
            buttonText=buttonText
        )
    
    click()
    return True

# Q: Will this help avoid detection on the steam release?
# A: Lol. Lmao even.