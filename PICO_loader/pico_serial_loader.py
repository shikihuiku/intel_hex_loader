#!/usr/bin/env python3
"""
PICO Serial Loader - Windows側スクリプト
Intel Hexファイルを読み込み、USB CDC経由でPICOに転送する
"""

import sys
import time
import serial
import serial.tools.list_ports
from pathlib import Path

# 親ディレクトリのintel_hex_loaderをインポート
sys.path.append(str(Path(__file__).parent.parent))
from intel_hex_loader import IntelHexLoader

# 定数
DEFAULT_BAUDRATE = 115200
CHUNK_SIZE = 128  # 一度に送信する最大バイト数
RESPONSE_TIMEOUT = 5.0  # レスポンスタイムアウト（秒）

class PicoSerialLoader:
    """PICOへのシリアル転送を管理するクラス"""
    
    def __init__(self, port=None, baudrate=DEFAULT_BAUDRATE, debug=False):
        """
        初期化
        
        Args:
            port: シリアルポート名（Noneの場合は自動検出）
            baudrate: ボーレート
            debug: デバッグモード
        """
        self.port = port
        self.baudrate = baudrate
        self.debug = debug
        self.serial = None
        
    def find_pico_port(self):
        """PICOのデータポートを自動検出"""
        ports = serial.tools.list_ports.comports()
        pico_ports = []
        
        for port in ports:
            # PICOのUSB VID/PIDをチェック
            if port.vid == 0x2E8A:  # Raspberry Pi VID
                pico_ports.append(port)
                if self.debug:
                    print(f"[DEBUG] Found PICO: {port.device} - {port.description}")
        
        if not pico_ports:
            raise RuntimeError("PICOが見つかりません。USBケーブルを確認してください。")
        
        # 複数のポートがある場合、データポートを選択
        # 通常、2番目のポートがデータ用
        if len(pico_ports) >= 2:
            data_port = pico_ports[1]
            if self.debug:
                print(f"[DEBUG] Using data port: {data_port.device}")
            return data_port.device
        else:
            # 1つしかない場合は、それを使用（main_simple.pyの場合）
            return pico_ports[0].device
    
    def connect(self):
        """シリアルポートに接続"""
        if not self.port:
            self.port = self.find_pico_port()
            print(f"自動検出されたポート: {self.port}")
        
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=8,
                parity='N',
                stopbits=1,
                timeout=1.0
            )
            # バッファをクリア
            self.serial.reset_input_buffer()
            self.serial.reset_output_buffer()
            
            print(f"接続しました: {self.port} @ {self.baudrate}bps")
            
        except serial.SerialException as e:
            raise RuntimeError(f"シリアルポートの接続に失敗しました: {e}")
    
    def disconnect(self):
        """シリアルポートを切断"""
        if self.serial and self.serial.is_open:
            self.serial.close()
            print("切断しました")
    
    def send_command(self, command):
        """コマンドを送信してレスポンスを待つ"""
        if not self.serial or not self.serial.is_open:
            raise RuntimeError("シリアルポートが開いていません")
        
        # 改行コードをCRLFに統一
        if not command.endswith('\r\n'):
            if command.endswith('\n'):
                command = command[:-1] + '\r\n'
            else:
                command += '\r\n'
        
        # コマンド送信
        if self.debug:
            print(f"[DEBUG] Sending: {command.strip()}")
        
        self.serial.write(command.encode())
        
        # レスポンスを待つ
        start_time = time.time()
        response = ""
        
        while time.time() - start_time < RESPONSE_TIMEOUT:
            if self.serial.in_waiting > 0:
                data = self.serial.readline()
                if data:
                    response = data.decode().strip()
                    if self.debug:
                        print(f"[DEBUG] Received: {response}")
                    break
            time.sleep(0.01)
        
        if not response:
            raise TimeoutError("レスポンスがタイムアウトしました")
        
        return response
    
    def parse_response(self, response):
        """レスポンスを解析"""
        parts = response.split(':', 1)
        if len(parts) != 2:
            return None, response
        
        status = parts[0]
        message = parts[1]
        
        return status, message
    
    def ping(self):
        """接続確認"""
        response = self.send_command("P\n")
        status, message = self.parse_response(response)
        
        if status != "OK" or message != "READY":
            raise RuntimeError(f"Ping失敗: {response}")
        
        return True
    
    def write_data(self, start_address, data):
        """データを書き込む"""
        # データを16進数文字列に変換
        hex_data = ''.join(f'{b:02X}' for b in data)
        
        # Writeコマンドを作成
        command = f"W:{start_address:02X}:{len(data):02X}:{hex_data}\n"
        
        # 送信
        response = self.send_command(command)
        status, message = self.parse_response(response)
        
        if status != "OK":
            raise RuntimeError(f"書き込みエラー: {response}")
        
        return True
    
    def end_transfer(self):
        """転送終了"""
        response = self.send_command("E\n")
        status, message = self.parse_response(response)
        
        if status != "OK":
            raise RuntimeError(f"終了エラー: {response}")
        
        return True
    
    def transfer_hex_file(self, hex_file):
        """Intel Hexファイルを転送"""
        # Hexファイルを読み込む
        loader = IntelHexLoader()
        loader.load_file(hex_file)
        
        print(f"\nHexファイル読み込み完了: {len(loader.memory)} バイト")
        
        # メモリマップを表示
        print("\nメモリマップ:")
        loader.print_memory_map()
        
        # 接続確認
        print("\nPICOに接続中...")
        if not self.ping():
            raise RuntimeError("PICOとの接続確認に失敗しました")
        
        print("接続確認OK")
        
        # データを転送
        print("\nデータ転送中...")
        total_bytes = len(loader.memory)
        transferred_bytes = 0
        
        # アドレス順にソートして、連続したデータをまとめて送信
        sorted_addresses = sorted(loader.memory.keys())
        
        i = 0
        while i < len(sorted_addresses):
            start_addr = sorted_addresses[i]
            data = [loader.memory[start_addr]]
            
            # 連続したアドレスのデータをまとめる
            j = i + 1
            while j < len(sorted_addresses) and len(data) < CHUNK_SIZE:
                if sorted_addresses[j] == start_addr + len(data):
                    data.append(loader.memory[sorted_addresses[j]])
                    j += 1
                else:
                    break
            
            # データを送信
            self.write_data(start_addr & 0xFF, bytes(data))
            
            transferred_bytes += len(data)
            progress = (transferred_bytes / total_bytes) * 100
            
            print(f"\r転送中... {transferred_bytes}/{total_bytes} バイト ({progress:.1f}%)", end='', flush=True)
            
            i = j
        
        print("\n\n転送完了")
        
        # 転送終了
        self.end_transfer()
        print("終了処理完了")


def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='PICO Serial Loader - Intel HexファイルをPICOに転送')
    parser.add_argument('hexfile', help='転送するIntel Hexファイル')
    parser.add_argument('-p', '--port', help='シリアルポート（省略時は自動検出）')
    parser.add_argument('-b', '--baudrate', type=int, default=DEFAULT_BAUDRATE,
                        help=f'ボーレート（デフォルト: {DEFAULT_BAUDRATE}）')
    parser.add_argument('-d', '--debug', action='store_true', help='デバッグモード')
    
    args = parser.parse_args()
    
    # ファイルの存在確認
    if not Path(args.hexfile).exists():
        print(f"エラー: ファイル '{args.hexfile}' が見つかりません")
        sys.exit(1)
    
    # ローダーを作成
    loader = PicoSerialLoader(port=args.port, baudrate=args.baudrate, debug=args.debug)
    
    try:
        # 接続
        loader.connect()
        
        # 転送
        loader.transfer_hex_file(args.hexfile)
        
    except Exception as e:
        print(f"\nエラー: {e}")
        sys.exit(1)
        
    finally:
        # 切断
        loader.disconnect()


if __name__ == "__main__":
    main()
