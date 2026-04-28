import numpy as np

def calculate_angle(a,b,c):
    a=np.array(a)
    b=np.array(b)
    c=np.array(c)
    
    ba = a - b
    bc = c - b
    
    #θ = arctan2(cross,dot)
    angle_rad=np.arctan2(ba[0]*bc[1]-ba[1]*bc[0],ba[0]*bc[0]+ba[1]*bc[1])
    angle = np.abs(angle_rad*180.0/np.pi)

    if angle>180.0:
        angle = 360.0-angle

    return angle    