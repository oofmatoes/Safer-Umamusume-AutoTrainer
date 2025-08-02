from paddleocr import PaddleOCR
from PIL import ImageGrab
import tempfile
import os
import cv2
import numpy as np
from core.safeClick import *

ocr = None

def initOcr():
    global ocr
    ocr = PaddleOCR(
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_angle_cls=False,
        lang='en',  
        text_det_thresh=0.5,      
        text_det_box_thresh=0.7, 
        text_recognition_batch_size=6,
        enable_mkldnn=True,
    )
    print("OCR loaded")

def getTextCords(topLeft, bottomRight):
    x1, y1 = topLeft
    x2, y2 = bottomRight
    bounds = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
    
    screenshot = ImageGrab.grab(bbox=bounds)
    
    width, height = screenshot.size
    if width > 500 or height > 500:
        ratio = min(500/width, 500/height)
        screenshot = screenshot.resize((int(width * ratio), int(height * ratio)))
        scaleFactor = ratio
    else:
        scaleFactor = 1.0
    
    fileDescriptor, tempPath = tempfile.mkstemp(suffix='.png')
    os.close(fileDescriptor)  
    screenshot.save(tempPath)
    ocrResult = ocr.predict(tempPath)
    
    textCoordinates = {}
    offsetX, offsetY = bounds[0], bounds[1]
    
    for result in ocrResult:
        for i in range(len(result['rec_texts'])):
            recognizedText = result['rec_texts'][i]
            polygon = result['rec_polys'][i]
            
            totalX = sum(point[0] / scaleFactor for point in polygon)
            totalY = sum(point[1] / scaleFactor for point in polygon)
            
            centerX = totalX / len(polygon) + offsetX
            centerY = totalY / len(polygon) + offsetY

            textCoordinates[recognizedText] = (centerX, centerY)
            
    return textCoordinates

def findAndClick(topLeft, bottomRight, searchText):
    textCoordinates = getTextCords(topLeft, bottomRight)
    
    for foundText, position in textCoordinates.items():
        if searchText in foundText:
            x, y = position
            return safeClick(x, y, searchText)
    
    return False

def getImageCords(topLeft, bottomRight, imagePath, threshold=0.8):
    x1, y1 = topLeft
    x2, y2 = bottomRight
    bounds = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
    
    screenshot = ImageGrab.grab(bbox=bounds)
    screenshotArray = np.array(screenshot)
    screenshotBGR = cv2.cvtColor(screenshotArray, cv2.COLOR_RGB2BGR)
    
    searchImage = cv2.imread(imagePath, cv2.IMREAD_COLOR)
    if searchImage is None:
        return {}
    
    imageCoordinates = {}
    offsetX, offsetY = bounds[0], bounds[1]
    
    scaleStep = 0.1
    currentScale = 0.5
    
    while currentScale <= 2.1:
        scaledWidth = int(searchImage.shape[1] * currentScale)
        scaledHeight = int(searchImage.shape[0] * currentScale)
        
        if scaledWidth > 0 and scaledHeight > 0 and scaledWidth <= screenshotBGR.shape[1] and scaledHeight <= screenshotBGR.shape[0]:
            scaledImage = cv2.resize(searchImage, (scaledWidth, scaledHeight))
            
            result = cv2.matchTemplate(screenshotBGR, scaledImage, cv2.TM_CCOEFF_NORMED)
            minVal, maxVal, minLoc, maxLoc = cv2.minMaxLoc(result)
            
            if maxVal >= threshold:
                centerX = maxLoc[0] + scaledWidth // 2 + offsetX
                centerY = maxLoc[1] + scaledHeight // 2 + offsetY
                imageCoordinates[f"image_{maxVal:.3f}_scale_{currentScale:.1f}"] = (centerX, centerY)
        
        currentScale += scaleStep
    
    return imageCoordinates

def findAndClickImage(topLeft, bottomRight, imagePath, threshold=0.8):
    imageCoordinates = getImageCords(topLeft, bottomRight, imagePath, threshold)
    
    if imageCoordinates:
        bestMatch = max(imageCoordinates.items(), key=lambda x: float(x[0].split('_')[1]))
        imageName, position = bestMatch
        x, y = position
        return safeClick(x, y, imageName)
    
    return False

def deduplicatePositions(positions, minDistance=30):
    if not positions:
        return []
    
    uniquePositions = []
    for pos in positions:
        x, y = pos
        isUnique = True
        for uniquePos in uniquePositions:
            ux, uy = uniquePos
            distance = ((x - ux) ** 2 + (y - uy) ** 2) ** 0.5
            if distance < minDistance:
                isUnique = False
                break
        if isUnique:
            uniquePositions.append(pos)
    
    return uniquePositions

def friendCheck(topLeft, bottomRight, currentTrainingType=None, isSeniorYear=False, threshold=0.86):
    supportsFolder = "assets\\supports"
    
    if not os.path.exists(supportsFolder):
        return 0
    
    allPositions = []
    totalScore = 0
    
    for filename in os.listdir(supportsFolder):
        if filename.lower().endswith(('.png')):
            imagePath = os.path.join(supportsFolder, filename)
            imageCoordinates = getImageCords(topLeft, bottomRight, imagePath, threshold)
            
            if imageCoordinates:
                bestMatch = max(imageCoordinates.items(), key=lambda x: float(x[0].split('_')[1]))
                _, position = bestMatch
                allPositions.append(position)
                
                if currentTrainingType:
                    filenameLower = filename.lower()
                    trainingTypeLower = currentTrainingType.lower()
                    
                    if filenameLower.endswith(f"_{trainingTypeLower}.png") and isSeniorYear:
                        totalScore += 2
                    else:
                        totalScore += 1
                else:
                    totalScore += 1
    
    uniquePositions = deduplicatePositions(allPositions)
    
    if currentTrainingType:
        matchingTypeCount = 0
        nonMatchingCount = 0
        
        for filename in os.listdir(supportsFolder):
            if filename.lower().endswith(('.png')):
                imagePath = os.path.join(supportsFolder, filename)
                imageCoordinates = getImageCords(topLeft, bottomRight, imagePath, threshold)
                
                if imageCoordinates:
                    filenameLower = filename.lower()
                    trainingTypeLower = currentTrainingType.lower()
                    
                    if filenameLower.endswith(f"_{trainingTypeLower}.png"):
                        matchingTypeCount += 1
                    else:
                        nonMatchingCount += 1
        
        uniqueMatchingPositions = deduplicatePositions([pos for i, pos in enumerate(allPositions) if i < matchingTypeCount])
        uniqueNonMatchingPositions = deduplicatePositions([pos for i, pos in enumerate(allPositions) if i >= matchingTypeCount])
        
        if isSeniorYear:
            finalScore = len(uniqueMatchingPositions) * 2 + len(uniqueNonMatchingPositions)
        else:
            finalScore = len(uniquePositions)
        return finalScore
    else:
        friendCount = len(uniquePositions)
        return friendCount