import math


class GestureAnalyz:
    def __init__(self):
        self.landmarks = None

        self.tips = [4,8,12,16,20]
        self.pips = [2,6,10,14,18]

        self.gestures = {
            (0, 0, 0, 0, 0): "FIST",
            (0, 1, 0, 0, 0): "POINT", 
            (0, 1, 1, 0, 0): "PEACE",  
            (1, 1, 1, 1, 1): "OPEN HAND",        
            (1, 0, 0, 0, 0): "THUMBS" 
        }
    
    def is_finger_up(self,tip, pip):

        return tip.y < pip.y
    
    def get_distance(self, p1, p2):
        return math.sqrt((p1.x-p2.x)**2 + (p1.y-p2.y)**2)
    
    def get_gesture(self, landmarks):
        if not landmarks:
            return None
        
        fingers_status = []

        for i in range(1, 5):
            tip_landmark = landmarks[self.tips[i]]
            pip_landmark = landmarks[self.pips[i]]
            
            if self.is_finger_up(tip_landmark, pip_landmark):
                fingers_status.append(1) 
            else:
                fingers_status.append(0)

        thumb_tip = landmarks[self.tips[0]]
        thumb_mcp = landmarks[self.pips[0]]
        pinky_mcp = landmarks[17]

        tip_distance = self.get_distance(thumb_tip, pinky_mcp)
        base_distance = self.get_distance(thumb_mcp, pinky_mcp)

      
        if tip_distance > base_distance:
            fingers_status.insert(0, 1) 
        else:
            fingers_status.insert(0, 0)

        gesture_tuple = tuple(fingers_status)

        return self.gestures.get(gesture_tuple, "unknown_gesture")