"""
Raspberry Pi PICO用 Intel Hex Loader (USB CDCバージョン)
MicroPythonで動作し、USB CDC経由で受信したデータをGPIOに出力する
標準入出力とは独立してUSBシリアルを使用するため、print()でのデバッグが可能
"""

import machine
import time
import usb_cdc

# GPIO設定
ADDR_PINS = [0, 1, 2, 3, 4, 5, 6, 7]     # アドレスバス (GPIO 0-7)
DATA_PINS = [8, 9, 10, 11, 12, 13, 14, 15]  # データバス (GPIO 8-15)
WE_PIN = 16  # /WE (Write Enable) 信号 - Active Low

# デバッグモード
DEBUG = True  # USB CDCを使うので、print()でのデバッグが可能

class PicoHexLoader:
    def __init__(self):
        """GPIOとシリアル通信の初期化"""
        # USB CDCシリアルポートを取得
        try:
            if not usb_cdc.data:
                raise ValueError("USB CDC data port not available. Please enable it in boot.py")
            self.serial = usb_cdc.data
            self.serial.timeout = 0.1  # 100msタイムアウト
        except Exception as e:
            print(f"Error: USB CDC initialization failed: {e}")
            print("Please ensure boot.py contains: usb_cdc.enable(console=True, data=True)")
            raise
        
        # 受信バッファ
        self.rx_buffer = bytearray()
        
        # アドレスバスの設定
        self.addr_pins = []
        for pin in ADDR_PINS:
            p = machine.Pin(pin, machine.Pin.OUT)
            p.value(0)
            self.addr_pins.append(p)
        
        # データバスの設定
        self.data_pins = []
        for pin in DATA_PINS:
            p = machine.Pin(pin, machine.Pin.OUT)
            p.value(0)
            self.data_pins.append(p)
        
        # /WE信号の設定（初期値はHigh = 非アクティブ）
        self.we_pin = machine.Pin(WE_PIN, machine.Pin.OUT)
        self.we_pin.value(1)
        
        if DEBUG:
            print("[DEBUG] GPIO and USB CDC initialized")
    
    def write_byte(self, address, data):
        """1バイトをGPIOに出力"""
        # /WE信号をHigh（非アクティブ）にする
        self.we_pin.value(1)
        
        # アドレスを設定
        for i in range(8):
            self.addr_pins[i].value((address >> i) & 1)
        
        # データを設定
        for i in range(8):
            self.data_pins[i].value((data >> i) & 1)
        
        # /WE信号をLow（アクティブ）にして書き込み
        self.we_pin.value(0)
        time.sleep_ms(10)  # 10ms待機
        
        # /WE信号をHigh（非アクティブ）に戻す
        self.we_pin.value(1)
        time.sleep_ms(10)  # 10ms待機
        
        if DEBUG:
            print(f"[DEBUG] Write: ADDR=0x{address:02X}, DATA=0x{data:02X}, /WE=0 (active)")
    
    def parse_command(self, line):
        """コマンドを解析"""
        line = line.strip()
        
        # 単一文字コマンド
        if len(line) == 1:
            if line in ['P', 'E']:
                return {'cmd': line}
            else:
                return {'error': 'COMMAND', 'message': f'Unknown command: {line}'}
        
        # Writeコマンド
        if line.startswith('W:'):
            try:
                parts = line.split(':', 3)
                if len(parts) != 4:
                    return {'error': 'FORMAT', 'message': 'Invalid write format'}
                
                start_address = int(parts[1], 16)
                length = int(parts[2], 16)
                hex_data = parts[3]
                
                # データ長チェック
                if length == 0 or length > 255:
                    return {'error': 'LENGTH', 'message': f'Invalid length: {length}'}
                
                if len(hex_data) != length * 2:
                    return {'error': 'LENGTH', 'message': f'Expected {length*2} hex chars, got {len(hex_data)}'}
                
                # 16進数文字列をバイト配列に変換
                data = []
                for i in range(0, len(hex_data), 2):
                    data.append(int(hex_data[i:i+2], 16))
                
                return {
                    'cmd': 'W',
                    'start_address': start_address,
                    'length': length,
                    'data': data
                }
                
            except Exception as e:
                return {'error': 'FORMAT', 'message': str(e)}
        
        return {'error': 'COMMAND', 'message': f'Unknown command: {line}'}
    
    def send_response(self, status, message):
        """レスポンスを送信"""
        response = f"{status}:{message}\n"
        self.serial.write(response.encode())
        if DEBUG:
            print(f"[DEBUG] Sent: {response.strip()}")
    
    def handle_write_command(self, start_address, length, data):
        """Writeコマンドを処理"""
        if DEBUG:
            print(f"[DEBUG] Write command: START_ADDR=0x{start_address:02X}, LENGTH={length}")
        
        # 各バイトを書き込み
        for i in range(length):
            address = (start_address + i) & 0xFF  # 8ビットアドレスに制限
            self.write_byte(address, data[i])
            
            if DEBUG:
                print(f"[DEBUG] Writing byte {i+1}/{length}: ADDR=0x{address:02X}, DATA=0x{data[i]:02X}")
        
        self.send_response("OK", "WRITE")
    
    def read_line(self):
        """シリアルから1行読み込み（CRLF/LF対応）- ノンブロッキング"""
        MAX_LINE_LENGTH = 1024  # 最大行長
        
        # 新しいデータを読み込み
        data = self.serial.read()
        if data:
            self.rx_buffer.extend(data)
        
        # バッファサイズチェック
        if len(self.rx_buffer) > MAX_LINE_LENGTH:
            # 長すぎる行は破棄
            self.rx_buffer = bytearray()
            return None
        
        # 改行文字を探す（\n or \r\n）
        newline_pos = self.rx_buffer.find(b'\n')
        if newline_pos >= 0:
            # 改行までのデータを取得
            line_data = self.rx_buffer[:newline_pos]
            # CRLFの場合、CRを削除
            if line_data.endswith(b'\r'):
                line_data = line_data[:-1]
            
            try:
                line = line_data.decode('utf-8')
            except UnicodeDecodeError:
                # デコードエラーは無視
                self.rx_buffer = self.rx_buffer[newline_pos + 1:]
                return None
            
            # バッファから削除
            self.rx_buffer = self.rx_buffer[newline_pos + 1:]
            return line
        
        # 完全な行がまだない
        return None
    
    def run(self):
        """メインループ"""
        print("PICO Hex Loader (USB CDC) started")
        self.send_response("OK", "READY")
        
        while True:
            try:
                # シリアルからの入力を読み込む（ノンブロッキング）
                line = self.read_line()
                if not line:
                    # データがない場合は少し待つ
                    time.sleep_ms(10)
                    continue
                
                if DEBUG:
                    print(f"[DEBUG] Received: {line}")
                
                # コマンドを解析
                result = self.parse_command(line)
                
                if 'error' in result:
                    self.send_response("ERR", result['error'])
                    continue
                
                cmd = result['cmd']
                
                # コマンドごとの処理
                if cmd == 'P':
                    self.send_response("OK", "READY")
                
                elif cmd == 'W':
                    self.handle_write_command(
                        result['start_address'],
                        result['length'],
                        result['data']
                    )
                
                elif cmd == 'E':
                    self.send_response("OK", "END")
                    # 必要に応じてGPIOをリセット
                    for pin in self.addr_pins + self.data_pins:
                        pin.value(0)
                    self.we_pin.value(1)
                
            except Exception as e:
                if DEBUG:
                    print(f"[DEBUG] Error: {e}")
                self.send_response("ERR", "FORMAT")


# メイン実行
if __name__ == "__main__":
    loader = PicoHexLoader()
    loader.run()
