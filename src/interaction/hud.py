import cv2 as cv


class HUD:

    def __init__(self):
        self.font = cv.FONT_HERSHEY_SIMPLEX
        self.font_scale = 0.6
        self.thickness = 1
        self.margin_x = 20
        self.line_height = 25

    def draw(self, frame, data):
        
        overlay = frame.copy()
        cv.rectangle(overlay, (10, 10), (300, 120), (0, 0, 0), -1)
        cv.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)

       
        cv.putText(frame,
                   f"Gesture : {data.get('gesture', 'None')}",
                   (self.margin_x, 35),
                   self.font, self.font_scale, (200, 200, 0), self.thickness, cv.LINE_AA)

       
        cv.putText(frame,
                   f"Action  : {data.get('action', 'None')}",
                   (self.margin_x, 35 + self.line_height),
                   self.font, self.font_scale, (0, 250, 160), self.thickness, cv.LINE_AA)

   
        cv.putText(frame,
                   f"Exercise: {data.get('exercise', 'None')}",
                   (self.margin_x, 35 + self.line_height * 2),
                   self.font, self.font_scale, (0, 255, 255), self.thickness + 1, cv.LINE_AA)

       
        cv.putText(frame,
                   f"Status  : {data.get('system', 'ACTIVE')}",
                   (self.margin_x, 35 + self.line_height * 3),
                   self.font, self.font_scale, data.get("color", (0, 255, 0)), self.thickness, cv.LINE_AA)

        
        h, w = frame.shape[:2]
        sk_txt = "SKELETON: ON" if data.get("skeleton", True) else "SKELETON: OFF"
        sk_color = (0, 255, 0) if data.get("skeleton", True) else (0, 0, 255)
        cv.putText(frame, sk_txt, (self.margin_x, h - 20),
                   self.font, 0.55, sk_color, 1, cv.LINE_AA)

        return frame