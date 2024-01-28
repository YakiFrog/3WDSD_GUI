import socket
import time

#----------------------------------------------------------------
global UDP_IP, UDP_PORT

UDP_IP = "192.168.39.118"
UDP_PORT = 12345

# グローバル変数を使用するための宣言
global sendV, sendVd, sendR

# グローバル変数の初期化
sendV, sendVd, sendR = 0, 0, 0
#---------------------------------------------------------------

def run_udp_communication(slider_queue):
    global sendV, sendVd, sendR
    global UDP_IP, UDP_PORT
    
    # ソケット作成
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    prev_time = time.time()
    send_interval = 1
    
    print("UDP通信を開始します")
    print("UDP IP: " + str(UDP_IP) + ", port: " + str(UDP_PORT))
    # サーバー側にデータを送信
    while True:
        try:
            current_time = time.time()
            # キューからデータを取得
            if slider_queue != None:
                if not slider_queue.empty():
                    sendV, sendVd, sendR = slider_queue.get()
            # 0.01 秒ごとにデータを送信
            if current_time - prev_time >= send_interval:
                send_data = (str(sendV) + "," + str(sendVd) + "," + str(sendR)).encode("utf-8") # bytes型に変換
                # 送信
                sock.sendto(send_data, (UDP_IP, UDP_PORT))
                # print("send: " + str(sendV) + ", " + str(sendVd) + ", " + str(sendR))
                prev_time = current_time
        except KeyboardInterrupt:
            print()
            break
        
    sock.close()
    print("UDP通信を終了しました")
    
def main(slider_queue):
    try:
        run_udp_communication(slider_queue)
    except Exception as e:
        print(e)
        
if __name__ == '__main__':
    main(slider_queue=None)
    print("MADE BY KOTANI")