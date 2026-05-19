import cv2 as cv


def _hex_to_bgr(hex_color: str) -> tuple:
    """'#2ECC71'  →  (113, 204, 46)  (BGR)"""
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return (b, g, r)


class HUD:

    def __init__(self):
        self.font        = cv.FONT_HERSHEY_SIMPLEX
        self.font_scale  = 0.6
        self.thickness   = 1
        self.margin_x    = 20
        self.line_height = 25



    def _text(self, frame, text, pos, color=(255, 255, 255), scale=None, thick=None):
        cv.putText(frame, text, pos,
                   self.font,
                   scale  if scale is not None else self.font_scale,
                   color,
                   thick  if thick is not None else self.thickness,
                   cv.LINE_AA)

    def _panel(self, frame, x1, y1, x2, y2, alpha=0.45):
        overlay = frame.copy()
        cv.rectangle(overlay, (x1, y1), (x2, y2), (0, 0, 0), -1)
        cv.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

   

    def draw(self, frame, data):
        h, w = frame.shape[:2]

        
        self._panel(frame, 10, 10, 310, 135)

        self._text(frame,
                   f"Gesture : {data.get('gesture', 'None')}",
                   (self.margin_x, 35),
                   color=(200, 200, 0))

        self._text(frame,
                   f"Action  : {data.get('action', 'None')}",
                   (self.margin_x, 35 + self.line_height),
                   color=(0, 250, 160))

        self._text(frame,
                   f"Exercise: {data.get('exercise', 'None')}",
                   (self.margin_x, 35 + self.line_height * 2),
                   color=(0, 255, 255), thick=self.thickness + 1)

        self._text(frame,
                   f"Status  : {data.get('system', 'ACTIVE')}",
                   (self.margin_x, 35 + self.line_height * 3),
                   color=data.get("color", (0, 255, 0)))

        self._text(frame,
                   f"Phase   : {data.get('phase', 'rest').upper()}",
                   (self.margin_x, 35 + self.line_height * 4),
                   color=(180, 180, 255))

       
        reps     = data.get("reps", 0)
        rep_txt  = str(reps)
        (tw, th), _ = cv.getTextSize(rep_txt, self.font, 2.8, 3)
        rx = w - tw - 25
        self._panel(frame, w - tw - 40, 10, w - 10, th + 30, alpha=0.45)
        cv.putText(frame, rep_txt, (rx, th + 15),
                   self.font, 2.8, (0, 220, 255), 3, cv.LINE_AA)
        self._text(frame, "REPS", (rx, th + 38),
                   color=(160, 160, 160), scale=0.5)

        
        fb_text  = data.get("feedback", "")
        fb_color = _hex_to_bgr(data.get("fb_color", "#2ECC71"))

        if fb_text:
            (fw, fh), _ = cv.getTextSize(fb_text, self.font, 0.7, 2)
            bx1 = self.margin_x - 8
            by1 = h - 55
            bx2 = bx1 + fw + 16
            by2 = h - 10

           
            cv.rectangle(frame, (bx1, by1), (bx1 + 4, by2), fb_color, -1)

            self._panel(frame, bx1 + 4, by1, bx2, by2, alpha=0.5)
            cv.putText(frame, fb_text, (self.margin_x + 6, h - 25),
                       self.font, 0.7, fb_color, 2, cv.LINE_AA)

     
        sk_txt   = "SKELETON: ON" if data.get("skeleton", True) else "SKELETON: OFF"
        sk_color = (0, 255, 0)    if data.get("skeleton", True) else (0, 0, 255)
        (sw, _), _ = cv.getTextSize(sk_txt, self.font, 0.55, 1)
        self._text(frame, sk_txt, (w - sw - 15, h - 15),
                   color=sk_color, scale=0.55)

        return frame