import multiprocessing as mp
import control_ui
import udp
import control_joy

if __name__ == '__main__':
    mp.freeze_support() # Windowsで必要
        
    """ キューの生成 """
    slider_queue = mp.Queue()
    joy_queue = mp.Queue()
    
    """ 並列処理 """
    # プロセスの生成
    p1 = mp.Process(target=control_ui.main, args=(slider_queue, joy_queue))
    p2 = mp.Process(target=udp.main, args=(slider_queue,))
    p3 = mp.Process(target=control_joy.main, args=(joy_queue,))
    
    try:
        # プロセスの開始
        p1.start()
        p2.start()
        p3.start()
        # プロセスの終了待ち
        p1.join()
        p2.join()
        p3.join()
    except KeyboardInterrupt:
        print()
        pass
    
    print("MADE BY KOTANI")