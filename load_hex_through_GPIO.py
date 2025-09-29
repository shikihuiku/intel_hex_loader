#!/usr/bin/python
# coding: utf-8

"""
Raspberry PiのGPIOを使用してIntel Hexファイルの内容を転送するプログラム
GPIO 0-15: データバス（下位8ビット：アドレス、上位8ビット：データ）
GPIO 16: Write Enable信号
"""

import sys
import time
try:
    import RPi.GPIO as GPIO
except ImportError:
    print("警告: RPi.GPIOモジュールが見つかりません。Raspberry Pi上で実行してください。")
    sys.exit(1)

from intel_hex_loader import IntelHexLoader, RecordType


def output_byte_through_gpio(addr: int, data: int):
    """1バイトをGPIOを通じて送信する"""
    
    # アドレスの下位8ビットをGPIO 0-7に設定
    for i in range(8):
        GPIO.output(i, (addr >> i) & 1)
    
    # データをGPIO 8-15に設定
    for i in range(8):
        GPIO.output(i + 8, (data >> i) & 1)
    
    # GPIO 16にWrite Enable信号設定
    GPIO.output(16, 1)
    # 書き込み時間（マイクロ秒単位で調整可能）
    time.sleep(0.001)  # 1ms
    
    # Write Enable信号をLowに設定
    GPIO.output(16, 0)
    # 次の書き込みまでの待機時間
    time.sleep(0.001)  # 1ms

def main():
    # コマンドライン引数の確認
    if len(sys.argv) < 2:
        print("使用方法: python load_hex_through_GPIO.py <hexファイル>")
        sys.exit(1)
    
    hex_file = sys.argv[1]
    
    try:
        print(f"=== Intel Hexファイル '{hex_file}' をGPIOを通じて送信 ===\n")
        
        # GPIO設定
        GPIO.setmode(GPIO.BCM)
        
        # GPIO 0-16を出力モードに設定
        for i in range(17):
            GPIO.setup(i, GPIO.OUT)
            GPIO.output(i, 0)  # 初期値はLow
        
        # Intel Hexファイルを読み込む
        loader = IntelHexLoader()
        loader.load_file(hex_file)
        
        print(f"ファイル読み込み完了: {len(loader.memory)} バイト")
        
        # 拡張アドレスレコードの警告
        has_extended_address = False
        for record in loader.records:
            if record.record_type in [RecordType.EXT_SEGMENT_ADDR, RecordType.EXT_LINEAR_ADDR]:
                has_extended_address = True
                print(f"警告: 拡張アドレスレコード (タイプ {record.record_type:02X}) が見つかりました")
                print(f"      このスクリプトは8ビットアドレスのみ対応しています")
                print(f"      アドレス 0x100 以降のデータは 0x00-0xFF に折り返されます\n")
                break
        
        # 進捗表示用
        total_bytes = len(loader.memory)
        bytes_sent = 0
        
        # メモリの内容を順番に送信
        # loader.memoryは辞書なので、アドレス順にソート
        for address in sorted(loader.memory.keys()):
            # データを送信（下位8ビットのアドレスのみ）
            output_byte_through_gpio(address & 0xFF, loader.memory[address])
            
            # 進捗表示
            bytes_sent += 1
            if bytes_sent % 100 == 0:
                progress = (bytes_sent / total_bytes) * 100
                print(f"送信中... {bytes_sent}/{total_bytes} バイト ({progress:.1f}%)")
        
        print(f"\n送信完了: {bytes_sent} バイト")
        
        # GPIO設定をリセット
        GPIO.cleanup()
        
    except FileNotFoundError:
        print(f"エラー: ファイル '{hex_file}' が見つかりません")
        sys.exit(1)
        
    except Exception as e:
        # エラー時もGPIOをクリーンアップ
        GPIO.cleanup()
        
        print(f"\nエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
