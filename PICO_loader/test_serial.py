#!/usr/bin/env python3
"""
PICO Serial通信の基本テストスクリプト
"""

import serial
import serial.tools.list_ports
import time
import sys

def find_pico_ports():
    """PICOのポートを検出"""
    ports = serial.tools.list_ports.comports()
    pico_ports = []
    
    for port in ports:
        print(f"Found port: {port.device} - {port.description}")
        if port.vid == 0x2E8A:  # Raspberry Pi VID
            pico_ports.append(port)
    
    return pico_ports

def test_basic_commands(port_name):
    """基本コマンドをテスト"""
    print(f"\n=== Testing port: {port_name} ===")
    
    try:
        # シリアルポートを開く
        ser = serial.Serial(
            port=port_name,
            baudrate=115200,
            timeout=2.0
        )
        
        # バッファクリア
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        time.sleep(0.5)
        
        # 初期メッセージを読む
        while ser.in_waiting > 0:
            response = ser.readline().decode().strip()
            print(f"Initial: {response}")
        
        # 1. Pingテスト
        print("\n1. Testing PING command...")
        ser.write(b"P\r\n")
        response = ser.readline().decode().strip()
        print(f"Response: {response}")
        
        # 2. 無効なコマンドテスト
        print("\n2. Testing invalid command...")
        ser.write(b"X\r\n")
        response = ser.readline().decode().strip()
        print(f"Response: {response}")
        
        # 3. Writeコマンドテスト（1バイト）
        print("\n3. Testing WRITE command (1 byte)...")
        ser.write(b"W:10:01:55\r\n")
        response = ser.readline().decode().strip()
        print(f"Response: {response}")
        
        # 4. Writeコマンドテスト（複数バイト）
        print("\n4. Testing WRITE command (4 bytes)...")
        ser.write(b"W:20:04:01020304\r\n")
        response = ser.readline().decode().strip()
        print(f"Response: {response}")
        
        # 5. フォーマットエラーテスト
        print("\n5. Testing format error...")
        ser.write(b"W:20:02:01\r\n")  # データ長不一致
        response = ser.readline().decode().strip()
        print(f"Response: {response}")
        
        # 6. Endコマンドテスト
        print("\n6. Testing END command...")
        ser.write(b"E\r\n")
        response = ser.readline().decode().strip()
        print(f"Response: {response}")
        
        ser.close()
        print("\nTest completed successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        return False
    
    return True

def main():
    print("PICO Serial Communication Test")
    print("==============================")
    
    # PICOポートを検出
    pico_ports = find_pico_ports()
    
    if not pico_ports:
        print("\nNo PICO found!")
        print("Please check:")
        print("1. PICO is connected via USB")
        print("2. boot.py and main.py are loaded")
        print("3. PICO has been reset")
        return
    
    print(f"\nFound {len(pico_ports)} PICO port(s)")
    
    # 各ポートをテスト
    for port in pico_ports:
        test_basic_commands(port.device)
        
    # データポートが2番目の場合
    if len(pico_ports) >= 2:
        print("\n\nTesting data port specifically...")
        test_basic_commands(pico_ports[1].device)

if __name__ == "__main__":
    main()
    
    print("\n" + "="*60)
    print("Next step: Test with actual hex file")
    print("="*60)
    print("\nRun the following command to test file transfer:")
    print("  python pico_serial_loader.py ../intel_hex_sample.hex -d")
    print("\nThis will transfer the sample Intel Hex file to PICO.")
