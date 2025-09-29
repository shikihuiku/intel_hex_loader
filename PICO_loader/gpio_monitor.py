"""
PICO GPIO Monitor - GPIO出力を監視するスクリプト（PICO上で実行）
別のPICOやロジックアナライザで信号を確認する際の参考
"""

import machine
import time

# モニタするGPIOピン
ADDR_PINS = [0, 1, 2, 3, 4, 5, 6, 7]     # アドレスバス
DATA_PINS = [8, 9, 10, 11, 12, 13, 14, 15]  # データバス
WE_PIN = 16  # /WE信号

def setup_gpio_as_input():
    """GPIOを入力モードに設定"""
    pins = {}
    
    # アドレスバス
    for i, pin_num in enumerate(ADDR_PINS):
        pins[f'A{i}'] = machine.Pin(pin_num, machine.Pin.IN, machine.Pin.PULL_DOWN)
    
    # データバス
    for i, pin_num in enumerate(DATA_PINS):
        pins[f'D{i}'] = machine.Pin(pin_num, machine.Pin.IN, machine.Pin.PULL_DOWN)
    
    # /WE信号（プルアップ - 通常High）
    pins['WE'] = machine.Pin(WE_PIN, machine.Pin.IN, machine.Pin.PULL_UP)
    
    return pins

def read_bus_values(pins):
    """バスの値を読み取る"""
    # アドレスバスの値
    addr = 0
    for i in range(8):
        if pins[f'A{i}'].value():
            addr |= (1 << i)
    
    # データバスの値
    data = 0
    for i in range(8):
        if pins[f'D{i}'].value():
            data |= (1 << i)
    
    # /WE信号
    we = pins['WE'].value()
    
    return addr, data, we

def monitor_gpio():
    """GPIO状態を監視"""
    print("GPIO Monitor Started")
    print("Monitoring Address, Data, and /WE signals...")
    print("Press Ctrl+C to stop")
    
    pins = setup_gpio_as_input()
    last_state = (None, None, None)
    write_edge_detected = False
    
    while True:
        try:
            addr, data, we = read_bus_values(pins)
            current_state = (addr, data, we)
            
            # /WE信号の立ち下がりエッジを検出（1→0）
            if last_state[2] == 1 and we == 0:
                write_edge_detected = True
            
            # /WE信号の立ち上がりエッジを検出（0→1）
            if last_state[2] == 0 and we == 1 and write_edge_detected:
                # 書き込み完了
                print(f"WRITE: Addr=0x{addr:02X}, Data=0x{data:02X}")
                write_edge_detected = False
            
            # 状態変化があった場合（デバッグ用）
            if current_state != last_state and False:  # Falseでデバッグ出力無効
                print(f"Addr=0x{addr:02X}, Data=0x{data:02X}, /WE={we}")
            
            last_state = current_state
            time.sleep_ms(1)
            
        except KeyboardInterrupt:
            print("\nMonitor stopped")
            break

if __name__ == "__main__":
    monitor_gpio()
