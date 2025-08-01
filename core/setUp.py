import raylib
import math
import threading
from pynput.mouse import Button, Listener
import ctypes
from PIL import ImageGrab
from utils.constants import *

class Point:
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

class Vector3:
    def __init__(self, x=0, y=0, z=0):
        self.x = x
        self.y = y
        self.z = z

class Overlay:
    def __init__(self):
        self.savedPositions = {}
        self.maxEnergyOffset = 60
        self.isMoving = False
        self.currentDraggingKey = None
        self.user32 = ctypes.windll.user32
        self.energyThreshold = 50
        self.lastEnergyCheck = 0
        self.energyCheckInterval = 1.0
        self.running = False
        self.initDefaultPositions()

    def initDefaultPositions(self):
        self.savedPositions = {
            "minEnergy": Vector3(ENERGY_BUTTONS[0], ENERGY_BUTTONS[1], 26),
            "infirmary": Vector3(INF_BUTTON[0], INF_BUTTON[1], 26),
            "SUPPORT_CARD_ICON_REGION1": Vector3(SUPPORT_CARD_ICON_REGION[0], SUPPORT_CARD_ICON_REGION[1], 26),
            "SUPPORT_CARD_ICON_REGION2": Vector3(SUPPORT_CARD_ICON_REGION[0] + SUPPORT_CARD_ICON_REGION[2], SUPPORT_CARD_ICON_REGION[1] + SUPPORT_CARD_ICON_REGION[3], 26),
            "MOOD_REGION1": Vector3(MOOD_REGION[0], MOOD_REGION[1], 26),
            "MOOD_REGION2": Vector3(MOOD_REGION[0] + MOOD_REGION[2], MOOD_REGION[1] + MOOD_REGION[3], 26),
            "TURN_REGION1": Vector3(TURN_REGION[0], TURN_REGION[1], 26),
            "TURN_REGION2": Vector3(TURN_REGION[0] + TURN_REGION[2], TURN_REGION[1] + TURN_REGION[3], 26),
            "MAIN_BUTTONS_REGION1": Vector3(MAIN_BUTTONS_REGION[0], MAIN_BUTTONS_REGION[1], 26),
            "MAIN_BUTTONS_REGION2": Vector3(MAIN_BUTTONS_REGION[0] + MAIN_BUTTONS_REGION[2], MAIN_BUTTONS_REGION[1] + MAIN_BUTTONS_REGION[3], 26),
            "YEAR_REGION1": Vector3(YEAR_REGION[0], YEAR_REGION[1], 26),
            "YEAR_REGION2": Vector3(YEAR_REGION[0] + YEAR_REGION[2], YEAR_REGION[1] + YEAR_REGION[3], 26),
            "CRITERIA_REGION1": Vector3(CRITERIA_REGION[0], CRITERIA_REGION[1], 26),
            "CRITERIA_REGION2": Vector3(CRITERIA_REGION[0] + CRITERIA_REGION[2], CRITERIA_REGION[1] + CRITERIA_REGION[3], 26),
            "SKILL_PTS_REGION1": Vector3(SKILL_PTS_REGION[0], SKILL_PTS_REGION[1], 26),
            "SKILL_PTS_REGION2": Vector3(SKILL_PTS_REGION[0] + SKILL_PTS_REGION[2], SKILL_PTS_REGION[1] + SKILL_PTS_REGION[3], 26),
            "SAFE_AREA_REGION1": Vector3(SAFE_AREA_REGION[0], SAFE_AREA_REGION[1], 26),
            "SAFE_AREA_REGION2": Vector3(SAFE_AREA_REGION[0] + SAFE_AREA_REGION[2], SAFE_AREA_REGION[1] + SAFE_AREA_REGION[3], 26),
            "STATUS_REGION1": Vector3(STATUS_REGION[0], STATUS_REGION[1], 26),
            "STATUS_REGION2": Vector3(STATUS_REGION[0] + STATUS_REGION[2], STATUS_REGION[1] + STATUS_REGION[3], 26),
            "PLAY_AREA_REGION1": Vector3(PLAY_AREA_REGION[0], PLAY_AREA_REGION[1], 26),
            "PLAY_AREA_REGION2": Vector3(PLAY_AREA_REGION[0] + PLAY_AREA_REGION[2], PLAY_AREA_REGION[1] + PLAY_AREA_REGION[3], 26)
        }
        self.maxEnergyOffset = ENERGY_BUTTONS[2]

    def getScreenSize(self):
        return self.user32.GetSystemMetrics(0), self.user32.GetSystemMetrics(1) - 1

    def getEnergyPercent(self):
        minPos = self.savedPositions["minEnergy"]
        low = int(minPos.x) + 1
        high = int(minPos.x) + self.maxEnergyOffset
        found = high + 1
        y = int(minPos.y)
        
        while low <= high:
            mid = low + (high - low) // 2
            color = ImageGrab.grab(bbox=(mid, y, mid+1, y+1)).getpixel((0, 0))
            r, g, b = color[:3]
            if abs(r - 118) <= 30 and abs(g - 118) <= 30 and abs(b - 118) <= 30:
                found = mid
                high = mid - 1
            else:
                low = mid + 1
        
        energyPixels = found - int(minPos.x)
        return min(100.0, (energyPixels * 100.0) / self.maxEnergyOffset)

    def onClick(self, x, y, button, pressed):
        if button == Button.left:
            if pressed:
                self.isMoving = True
                for key, vector in self.savedPositions.items():
                    if math.sqrt((x - vector.x) ** 2 + (y - vector.y) ** 2) < vector.z:
                        self.currentDraggingKey = key
                        break
                
                maxEnergyPos = Vector3(
                    self.savedPositions["minEnergy"].x + self.maxEnergyOffset,
                    self.savedPositions["minEnergy"].y,
                    self.savedPositions["minEnergy"].z
                )
                if math.sqrt((x - maxEnergyPos.x) ** 2 + (y - maxEnergyPos.y) ** 2) < maxEnergyPos.z:
                    self.currentDraggingKey = "maxEnergy"
            else:
                self.isMoving = False
                self.currentDraggingKey = None

    def onMove(self, x, y):
        if self.running:
            return
            
        if self.isMoving and self.currentDraggingKey:
            if self.currentDraggingKey == "maxEnergy":
                self.maxEnergyOffset = max(60, x - int(self.savedPositions["minEnergy"].x))
            else:
                self.savedPositions[self.currentDraggingKey] = Vector3(
                    x, y, self.savedPositions[self.currentDraggingKey].z
                )

    def setupHooks(self):
        def startListener():
            with Listener(on_click=self.onClick, on_move=self.onMove) as listener:
                listener.join()
        threading.Thread(target=startListener, daemon=True).start()

    def getRectangle(self, rectName):
        p1 = self.savedPositions[rectName + "1"]
        p2 = self.savedPositions[rectName + "2"]
        return ((min(p1.x, p2.x), min(p1.y, p2.y)),
                (max(p1.x, p2.x), max(p1.y, p2.y)))

    def setRunning(self, value):
        self.running = value

    def drawTextWithOutline(self, text, x, y, fontSize):
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx != 0 or dy != 0:
                    raylib.DrawText(text, x + dx, y + dy, fontSize, (0, 0, 0, 255))
        raylib.DrawText(text, x, y, fontSize, (255, 255, 255, 255))

    def renderOverlay(self):
        rectangleNames = ["SUPPORT_CARD_ICON_REGION", "MOOD_REGION", "TURN_REGION", "MAIN_BUTTONS_REGION", "YEAR_REGION", "CRITERIA_REGION", "SKILL_PTS_REGION", "SAFE_AREA_REGION", "STATUS_REGION", "PLAY_AREA_REGION"]
        rectangleInfo = {
            "SUPPORT_CARD_ICON_REGION": ((0, 0, 255, 255), "Place over support card circles."),
            "MOOD_REGION": ((255, 165, 0, 255), "Place over mood"),
            "TURN_REGION": ((100, 66, 66, 255), "Place over turn"),
            "MAIN_BUTTONS_REGION": ((255, 0, 0, 255), "Place over main buttons"),
            "YEAR_REGION": ((255, 255, 0, 255), "Place over year"),
            "CRITERIA_REGION": ((0, 128, 128, 255), "Place over race goals"),
            "SKILL_PTS_REGION": ((128, 128, 128, 255), "Place over skill points"),
            "SAFE_AREA_REGION": ((255, 192, 203, 255), "Place over safe area"),
            "STATUS_REGION": ((0, 255, 127, 255), "Place over status"),
            "PLAY_AREA_REGION": ((128, 0, 255, 255), "Place over play area")
        }

        screenWidth, screenHeight = self.getScreenSize()
        raylib.SetConfigFlags(raylib.FLAG_WINDOW_TRANSPARENT | raylib.FLAG_WINDOW_UNDECORATED | raylib.FLAG_WINDOW_TOPMOST | raylib.FLAG_WINDOW_MOUSE_PASSTHROUGH)
        raylib.InitWindow(screenWidth, screenHeight, b"autoUmaTrainer")
        raylib.SetTargetFPS(60)

        while not raylib.WindowShouldClose():
            if not self.running:
                maxEnergyPos = Vector3(
                    self.savedPositions["minEnergy"].x + self.maxEnergyOffset,
                    self.savedPositions["minEnergy"].y,
                    self.savedPositions["minEnergy"].z
                )
                
                raylib.BeginDrawing()
                raylib.ClearBackground((0, 0, 0, 0))

                minEnergy = self.savedPositions["minEnergy"]
                raylib.DrawCircle(int(minEnergy.x), int(minEnergy.y), int(minEnergy.z), (255, 0, 0, int(255 * 0.5)))
                raylib.DrawCircle(int(minEnergy.x), int(minEnergy.y), 3, (0, 0, 0, 255))
                self.drawTextWithOutline(b"Energy", int(minEnergy.x - 30), int(minEnergy.y - 40), 20)

                raylib.DrawCircle(int(maxEnergyPos.x), int(maxEnergyPos.y), int(maxEnergyPos.z), (0, 255, 0, int(255 * 0.5)))
                raylib.DrawCircle(int(maxEnergyPos.x), int(maxEnergyPos.y), 3, (0, 0, 0, 255))

                infirmary = self.savedPositions["infirmary"]
                raylib.DrawCircle(int(infirmary.x), int(infirmary.y), int(infirmary.z), (128, 0, 128, int(255 * 0.5)))
                raylib.DrawCircle(int(infirmary.x), int(infirmary.y), 3, (0, 0, 0, 255))
                self.drawTextWithOutline(b"Infirmary", int(infirmary.x - 40), int(infirmary.y - 40), 20)

                for rectName in rectangleNames:
                    topLeft, bottomRight = self.getRectangle(rectName)
                    color, name = rectangleInfo[rectName]
                    p1 = self.savedPositions[rectName + "1"]
                    p2 = self.savedPositions[rectName + "2"]

                    raylib.DrawCircle(int(p1.x), int(p1.y), int(p1.z), (color[0], color[1], color[2], int(color[3] * 0.5)))
                    raylib.DrawCircle(int(p1.x), int(p1.y), 3, (0, 0, 0, 255))
                    raylib.DrawCircle(int(p2.x), int(p2.y), int(p2.z), (color[0], color[1], color[2], int(color[3] * 0.5)))
                    raylib.DrawCircle(int(p2.x), int(p2.y), 3, (0, 0, 0, 255))

                    raylib.DrawRectangleLines(
                        int(topLeft[0]), int(topLeft[1]),
                        int(bottomRight[0] - topLeft[0]), int(bottomRight[1] - topLeft[1]),
                        color
                    )

                    centerX = (topLeft[0] + bottomRight[0]) / 2
                    centerY = (topLeft[1] + bottomRight[1]) / 2
                    textWidth = raylib.MeasureText(name.encode(), 20)
                    self.drawTextWithOutline(name.encode(), int(centerX - textWidth / 2), int(centerY - 10), 20)

                text = b"Press p once ready"
                textWidth = raylib.MeasureText(text, 20)
                self.drawTextWithOutline(text, screenWidth - textWidth - 10, 10, 20)
                raylib.EndDrawing()
            else:
                raylib.BeginDrawing()
                raylib.ClearBackground((0, 0, 0, 0))
                raylib.EndDrawing()

        raylib.CloseWindow()

    def run(self):
        self.setupHooks()
        self.renderOverlay()