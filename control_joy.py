import pygame as pyg
import math
import time

global V_joy, Vd_joy, R_joy

V_joy, Vd_joy, R_joy = 0, 0, 0

# 許容誤差
EPS = 0.25

def controller_init():
    while True:
        if pyg.joystick.get_count() > 0:
            joy = pyg.joystick.Joystick(0)
            joy.init()
            print("Joystick name: " + joy.get_name())
            print("Number of axes: " + str(joy.get_numaxes()))
            print("Number of buttons: " + str(joy.get_numbuttons()))
            print("Number of hats: " + str(joy.get_numhats()))
            print("Number of balls: " + str(joy.get_numballs()))
            
            return joy
        else:
            print("No joysticks available...")
            time.sleep(1)

def controller_input(joy_queue):
    global V_joy, Vd_joy, R_joy
    x, y = 0, 0
    theta = 0
    pyg.init() # pygameの初期化  
    pyg.joystick.init() # ジョイスティックの初期化
    joy = controller_init()
    print("Controller input start")
    while True:
        try:
            events = pyg.event.get()
            for event in events:
                if event.type == pyg.JOYBUTTONDOWN:
                    if joy.get_button(0):
                        V_joy = 0
                        Vd_joy = 0
                        R_joy = 0
                        print("Reset")
                        
                elif event.type == pyg.JOYAXISMOTION:
                    if (abs(joy.get_axis(0)) > EPS or abs(joy.get_axis(1)) > EPS):
                        x = float(joy.get_axis(0)) # -1 ~ 1
                        y = float(-joy.get_axis(1)) # -1 ~ 1
                        theta = math.atan2(y, x) # ラジアン
                        
                        V_joy = float(math.sqrt(x ** 2 + y ** 2)) # -1 ~ 1[m/s]
                        Vd_joy = float(theta * 180 / math.pi) # -180 ~ 180[deg]
                    else:
                        V_joy = 0
                        Vd_joy = 0
                        
                    if (abs(joy.get_axis(2)) > EPS or abs(joy.get_axis(3)) > EPS):
                        R_joy = float(joy.get_axis(2)) # [m/s]
                    else:
                        R_joy = 0
                        
                print("1: V: " + str(round(V_joy, 2)) + ", Vd: " + str(round(Vd_joy, 2)) + ", R: " + str(round(R_joy, 2)))
            if joy_queue != None:
                # キューを空にする
                while not joy_queue.empty():
                    joy_queue.get()
                joy_queue.put([V_joy, Vd_joy, R_joy]) # [m/s], [deg], [m/s]
                time.sleep(0.05)
                
            # もし，コントローラの接続が切れたら
            if pyg.joystick.get_count() == 0:
                print("Controller disconnected...")
                V_joy, Vd_joy, R_joy = 0, 0, 0
                joy_queue.put([V_joy, Vd_joy, R_joy]) # [m/s], [deg], [m/s]
                joy.quit()
                joy = controller_init()
            
        except KeyboardInterrupt:
            print()
            joy.quit()
            break
            
def main(joy_queue=None):
    try:
        controller_input(joy_queue)
    except Exception as e:
        print(e)
        
if __name__ == '__main__':
    main(joy_queue=None)
    print("MADE BY KOTANI")
