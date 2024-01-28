import math
import matplotlib.pyplot as plt
import matplotlib.widgets as wg
import numpy as np
import time

#################### 初期パラメータ #######################

# 車体の半径[m]（車輪の半径じゃないよ）→ 環状に車輪が配置されていると設定
R = 0.5
# 車輪の半径[m]: rpm指定で速度を表示させる
r = 0.035
# 車輪の数  
n = 3  

# 車体の正面（0度）を決めるための"オフセット"（ワールド座標系でy軸方向↑が正面とする）
# 3輪の場合は30度，4輪の場合は45度に設定すると良い．
init_direction = math.pi / 6

################# 変数初期化（触らないで） #################

# 車輪同士の間隔[rad]
wheel_spacing = 2 * math.pi / n
# 車体の向き（ワールド座標系から見た）
robot_direction_world = 0

"""  入力  """

# 移動速度 v = rw [m/s]
V = 0 
# 移動方向（ローカル座標系から見た）                          
move_direction_local = 0
# 回転速度  
angular_vel = 0

""""""

# ループ時間
dt = 0
last_time = 0

prev_Vx_list = [0] * 12
prev_Vy_list = [0] * 12

# 機体の座標 (ワールド座標系)
x, y = 0, 0

# 送信データ
sendV, sendVd, sendR = 0, 0, 0

#################### グラフの設定 #######################

# グラフの設定
fig, ax = plt.subplots(figsize=(6, 6), dpi=100)
ax.set_aspect('equal')
plt.suptitle('N-Wheel Swerve Drive Simulation \n MADE BY KOTANI', fontsize=16, backgroundcolor='white',
            bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.5'))

# スライダーの設定
fig.subplots_adjust(left=0.15, bottom=0.25, right=0.85, top=0.95)
global s_V, s_move_direction, s_angular_vel, s_n

ax_V = plt.axes([0.5 - 0.6 / 2, 0.15, 0.6, 0.03], aspect='auto')
ax_move_direction = plt.axes([0.5 - 0.6 / 2, 0.1, 0.6, 0.03], aspect='auto')
ax_angular_vel = plt.axes([0.5 - 0.6 / 2, 0.05, 0.6, 0.03], aspect='auto')
ax_n = plt.axes([0.5 - 0.6 / 2, 0.00, 0.6, 0.03], aspect='auto')

s_V = wg.Slider(ax_V, 'Velocity', -2.0, 2.0, valinit=V, valstep=0.0001, valfmt='%0.1f[m/s]')
s_move_direction = wg.Slider(ax_move_direction, 'Direction', -180, 180, valinit=move_direction_local, valstep=0.0001, valfmt='%0.1f[deg]')
s_angular_vel = wg.Slider(ax_angular_vel, 'Rotate', -2.0, 2.0, valinit=angular_vel, valstep=0.0001, valfmt='%0.1f[m/s]')
s_n = wg.Slider(ax_n, 'N', 3, 12, valinit=n, valstep=1, valfmt='%0.1f')

#################### グラフの更新 #######################

V_key = 0
Vd_key = 0
R_key = 0

V_joy = 0
Vd_joy = 0
R_joy = 0

def key_press(event):
    # グローバル変数を使用するための宣言
    global V_key, Vd_key, R_key
    # キーが押されたとき
    if event.key == 'up':
        # V_key = 0.1 + s_V.val
        V_key = 0.5 + (s_V.val * 1)
    if event.key == 'down':
        # V_key = -0.1 + s_V.val
        V_key = -0.5 + (s_V.val * 1)
    if event.key == 'right':
        Vd_key = 10 + s_move_direction.val
    if event.key == 'left':
        Vd_key = -10 + s_move_direction.val
    if event.key == 'd':
        R_key = 1.0 + (s_angular_vel.val * 1)
    if event.key == 'a':
        R_key = -1.0 + (s_angular_vel.val * 1)
        
    # reset
    if event.key == 'r':
        V_key = 0
        Vd_key = 0
        R_key = 0
        
    # 範囲外になったら修正
    if V_key > 2.0:
        V_key = 2.0
    if V_key < -2.0:
        V_key = -2.0
    if Vd_key > 180:
        Vd_key = 180
    if Vd_key < -180:
        Vd_key = -180
    if R_key > 2.0:
        R_key = 2.0
    if R_key < -2.0:
        R_key = -2.0
        
    # スライダーの値を更新        
    s_V.set_val(V_key)
    s_move_direction.set_val(Vd_key)
    s_angular_vel.set_val(R_key)

def controller_update(joy_queue):
    # グローバル変数を使用するための宣言
    global V_joy, Vd_joy, R_joy
    # キューからデータを取得
    if joy_queue != None:
        if not joy_queue.empty():
            V_joy, Vd_joy, R_joy = joy_queue.get()
            # スライダーの値を更新
            s_V.set_val(V_joy * 2.0)
            s_move_direction.set_val(Vd_joy)
            s_angular_vel.set_val(R_joy * 2.0)
        else:
            pass
    else:
        pass
    
    
def update(slider_queue):
    # グローバル変数を使用するための宣言
    global x, y, init_direction, move_direction_local, robot_direction_world, dt, last_time, n, wheel_spacing, R, V, angular_vel, prev_Vx_list, prev_Vy_list
    global sendV, sendVd, sendR
    # key_pressで値を変更
    fig.canvas.mpl_connect('key_press_event', key_press)
    
    # スライダーの値を取得(デフォルトでは反時計回りが正だが，直感的には時計回りが正なので-1を掛けて反転)
    V = s_V.val # [m/s]
    move_direction_local = s_move_direction.val * math.pi / 180 # deg to rad
    angular_vel = -1 * s_angular_vel.val # TODO: [m/s] to [rad/s] にしないといけない
    n = int(s_n.val)
    
    # キューにデータを入れる
    if slider_queue != None:
        # キューの中身を空にする
        while not slider_queue.empty():
            slider_queue.get()
        # 小数点第2位までに丸める
        sendV = round(s_V.val, 2)
        sendVd = round(s_move_direction.val, 2)
        sendR = round(s_angular_vel.val, 2)
        # キューにデータを入れる
        slider_queue.put([sendV, sendVd, sendR])
    
    # 車輪同士の間隔を計算(車輪の数が変わったときに対応)
    wheel_spacing = 2 * math.pi / n
    
    # ループ時間を計算
    dt = time.time() - last_time
    last_time = time.time()
    
    # 車体の向きを計算（ワールド座標系）# TODO: [m/s] to [rad/s]にしているつもり(間違っているかも)
    robot_direction_world += (angular_vel / R) * dt
    
    # 回転行列 (車体の向きを基準にする）
    # (ローカル座標系 → ワールド座標系)
    rot = np.array([[math.cos(robot_direction_world), -math.sin(robot_direction_world)],
            [math.sin(robot_direction_world), math.cos(robot_direction_world)]])  
    
    # V, move_direction_localからVx, Vyを計算
    # Vx, Vy (ローカル座標系)
    Vx = V * math.cos(move_direction_local + math.pi / 2 - robot_direction_world - math.pi / 2)
    Vy = V * math.sin(move_direction_local + math.pi / 2 - robot_direction_world - math.pi / 2)
    
    # 車体の向きを考慮したVx,Vyを計算（ローカル座標系 → ワールド座標系）
    Vx, Vy = rot.dot(np.array([Vx, Vy]))  
    
    # 各車輪の速度ベクトルを格納するリスト
    Vx_list = [0] * n
    Vy_list = [0] * n
    
    # 各車輪の速度ベクトルを計算(このx,yの平方を取れば速度．角度を取れば旋回角度)
    for i in range(n):  # v = r * omega. ここでは，r = R, omega = angular_vel[rad/s]
        Vx_list[i] = Vx + R * math.cos(init_direction + wheel_spacing * i + math.pi / 2) * angular_vel
        Vy_list[i] = Vy + R * math.sin(init_direction + wheel_spacing * i + math.pi / 2) * angular_vel
        
        # 車体の向きを考慮した速度ベクトルの向きを計算(ローカル座標系 → ワールド座標系）
        Vx_list[i],  Vy_list[i] = rot.dot(np.array([Vx_list[i], Vy_list[i]]))
        
    ############################# モータのモデル化(1次遅れ) ################################
    
    K = 0.95 # 実際では入力値よりも出力値が小さくなるとして，その比率を表すゲイン
    T = 0.05278 # 時定数（52.78ms) ← M2006のモータの時定数. つまり，目標値に達するまでの時間がM2006と同じになる
    for i in range(n):
        Vx_list[i] = K * (1 - math.exp(-dt / T)) * Vx_list[i] + prev_Vx_list[i] * math.exp(-dt / T)
        Vy_list[i] = K * (1 - math.exp(-dt / T)) * Vy_list[i] + prev_Vy_list[i] * math.exp(-dt / T)
        prev_Vx_list[i] = Vx_list[i]
        prev_Vy_list[i] = Vy_list[i]
        
        # 車体の座標を更新（各車輪の速度ベクトルの平均をつかっている）
        x += Vx_list[i] * dt / n
        y += Vy_list[i] * dt / n
        
    #####################################################################################
    
    # グラフにあるものを全て削除（連続的に描画するため）
    ax.cla()
    ax.set_aspect('equal')
    ax.grid()
    # 描画の範囲を設定
    ax.set_xlim(x - 1.5, x + 1.5)
    ax.set_ylim(y - 1.5, y + 1.5)  
    # 車体の軸を描画(ローカル座標系のx軸，y軸)
    ax.plot([x, (x + 0.5 * math.cos(robot_direction_world))], [y, (y + 0.5 * math.sin(robot_direction_world))], color='red')
    ax.plot([x, (x + 0.5 * math.cos(robot_direction_world + math.pi / 2))], [y, (y + 0.5 * math.sin(robot_direction_world + math.pi / 2))], color='blue')
    # 車体の原点を描画
    ax.plot(x, y, color='black', marker='o')
    
    # 車輪の座標を格納するリスト(ローカル座標系)
    Q_list = []
    # n個の車輪の座標を計算し，その点から速度ベクトルを描画(ローカル座標系)
    for i in range(n):
        Q_list.append(ax.quiver(R * math.cos(init_direction + wheel_spacing * i), R * math.sin(init_direction + wheel_spacing * i), 
                                Vx_list[i] * 0.5, Vy_list[i] * 0.5, angles='xy', scale_units='xy', scale=1, color='red'))
        
    # 車体の向きを考慮した車輪の座標を計算し，車輪を描画(ワールド座標系) 
    for i in range(n):
        # 車体の向きを考慮した車輪の座標を計算 (ローカル座標系 → ワールド座標系)
        x_a, y_a = rot.dot(np.array([R * math.cos(init_direction + wheel_spacing * i), R * math.sin(init_direction + wheel_spacing * i)]))
        # 車輪を描画
        Q_list[i].set_offsets(np.array([x + x_a, y + y_a]))  
        
    ############################# ここから下は見た目を良くする表示物 ############################
    
    # 車輪同士を線で結ぶ
    for i in range(n):
        if i == n - 1: # 最後の車輪と最初の車輪を結ぶ
            x_a, y_a = rot.dot(np.array([R * math.cos(init_direction + wheel_spacing * i), R * math.sin(init_direction + wheel_spacing * i)]))
            x_b, y_b = rot.dot(np.array([R * math.cos(init_direction + wheel_spacing * 0), R * math.sin(init_direction + wheel_spacing * 0)]))
            # 車輪同士を結ぶ線を描画
            ax.plot([x + x_a, x + x_b], [y + y_a, y + y_b], color='black')
        else: # それ以外の車輪同士を結ぶ
            x_a, y_a = rot.dot(np.array([R * math.cos(init_direction + wheel_spacing * i), R * math.sin(init_direction + wheel_spacing * i)]))
            x_b, y_b = rot.dot(np.array([R * math.cos(init_direction + wheel_spacing * (i + 1)), R * math.sin(init_direction + wheel_spacing * (i + 1))]))
            # 車輪同士を結ぶ線を描画
            ax.plot([x + x_a, x + x_b], [y + y_a, y + y_b], color='black')
        
    # 車輪の番号，速度，角度を描画（文字）
    for i in range(n):
        # 各車輪の速度ベクトルをワールド座標系 → ローカル座標系に変換，車輪の旋回角度を求めるため．（旋回角度はローカル座標系）
        Vx_list[i],  Vy_list[i] = rot.T.dot(np.array([Vx_list[i], Vy_list[i]])) 
        # 車体の向きを考慮した各車輪の座標を計算 (ローカル座標系 → ワールド座標系)．車輪の番号，速度，角度を描画するため．
        x_a, y_a = rot.dot(np.array([R * math.cos(init_direction + wheel_spacing * i), R * math.sin(init_direction + wheel_spacing * i)]))
        # 各車輪の座標上に文字を描画
        ax.text(x + x_a, y + y_a, str(i + 1) + '\n' + 'Vel: ' + str(round(math.sqrt(Vx_list[i] ** 2 + Vy_list[i] ** 2), 2)) 
                + '\n' + 'Deg: ' + str(round((math.atan2(Vy_list[i], Vx_list[i]) * 180 / math.pi) % 360, 2)), 
                color='black', size=10, bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.2', alpha=0.8))
        
    # 車体の移動速度を計算
    Vx_ave = 0
    Vy_ave = 0
    
    # 各車輪の速度ベクトルの平均より車体の移動速度を計算
    for i in range(n):
        Vx_ave += abs(Vx_list[i]) / n
        Vy_ave += abs(Vy_list[i]) / n
        
    # 車体の移動速度を描画
    ax.text(x, y - 1, 'Vel: {:.2f} [m/s]\n Deg: {:.2f} [deg]'.format(math.sqrt(Vx_ave ** 2 + Vy_ave ** 2), (robot_direction_world * 180 / math.pi) % 360),
            color='black', size=12, ha='center', bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.2', alpha=0.8))
    
    fig.canvas.draw_idle() 

def main(slider_queue=None, joy_queue=None):
    while True:
        try:
            controller_update(joy_queue)
            update(slider_queue)
            plt.pause(0.01)
            if not plt.fignum_exists(fig.number):
                break
        except KeyboardInterrupt:
            print()
            break
        
if __name__ == '__main__':
    main(slider_queue=None, joy_queue=None)
    print("MADE BY KOTANI")