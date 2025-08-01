import threading
from pynput import keyboard
from core.logic import *
from utils.constants import *
from  core.betterOcr import *
from  core.setUp import *

initOcr()

pPressedEvent = threading.Event()
overlayInstance = None 

def onKeyPress(key):
    global overlayInstance
    try:
        if key.char == 'p':
            if overlayInstance:
                print(overlayInstance.savedPositions)
                convertAndWriteConstants()
                overlayInstance.setRunning(True)
                print("reached")
            pPressedEvent.set()
    except Exception:
        pass

def convertAndWriteConstants():
    global overlayInstance
    if not overlayInstance:
        return
    
    positions = overlayInstance.savedPositions
    
    def getRectangleFromPoints(region_name):
        p1 = positions[region_name + "1"]
        p2 = positions[region_name + "2"]
        
        left = min(p1.x, p2.x)
        top = min(p1.y, p2.y)
        right = max(p1.x, p2.x)
        bottom = max(p1.y, p2.y)
        
        width = right - left
        height = bottom - top
        
        return (int(left), int(top), int(width), int(height))
    
    support_card_region = getRectangleFromPoints("SUPPORT_CARD_ICON_REGION")
    mood_region = getRectangleFromPoints("MOOD_REGION")
    turn_region = getRectangleFromPoints("TURN_REGION")
    main_buttons_region = getRectangleFromPoints("MAIN_BUTTONS_REGION")
    year_region = getRectangleFromPoints("YEAR_REGION")
    criteria_region = getRectangleFromPoints("CRITERIA_REGION")
    skill_pts_region = getRectangleFromPoints("SKILL_PTS_REGION")
    safe_area_region = getRectangleFromPoints("SAFE_AREA_REGION")
    status_region = getRectangleFromPoints("STATUS_REGION")
    play_area_region = getRectangleFromPoints("PLAY_AREA_REGION")
    
    energy_buttons = (int(positions["minEnergy"].x), int(positions["minEnergy"].y), int(overlayInstance.maxEnergyOffset))
    inf_button = (int(positions["infirmary"].x), int(positions["infirmary"].y))
    
    constants_content = f'''SUPPORT_CARD_ICON_REGION={support_card_region}
MOOD_REGION={mood_region}
TURN_REGION={turn_region}
MAIN_BUTTONS_REGION={main_buttons_region}
YEAR_REGION={year_region}
CRITERIA_REGION={criteria_region}
SKILL_PTS_REGION={skill_pts_region}
PLAY_AREA_REGION={play_area_region}
SAFE_AREA_REGION={safe_area_region}
STATUS_REGION={status_region}
ENERGY_BUTTONS={energy_buttons}
INF_BUTTON={inf_button}
MOOD_LIST = ["AWFUL", "BAD", "NORMAL", "GOOD", "GREAT", "UNKNOWN"]
'''
    
    with open("utils/constants.py", "w") as file:
        file.write(constants_content)
    

def waitForP():
    with keyboard.Listener(on_press=onKeyPress) as listener:
        listener.join()

def main():
    global overlayInstance
    
    overlayInstance = Overlay()
    overlayThread = threading.Thread(target=overlayInstance.run, daemon=True)
    overlayThread.start()
    
    keyboardThread = threading.Thread(target=waitForP, daemon=True)
    keyboardThread.start()
    
    pPressedEvent.wait()
    mainLoop()

if __name__ == "__main__":
    main()