# Intel Hex PICO Loader

WindowsとRaspberry Pi PICOをシリアルポートで接続して、Intel Hexファイルの内容をPICOのGPIOピンに出力するシステムです。

## 概要

- Windows側でIntel Hexファイルを読み込み、USB CDC経由でPICOに転送
- PICOはMicroPythonで動作し、受信したデータをGPIOに出力
- 8ビットアドレス空間（0x00-0xFF）のみ対応

## システム構成

### PICO側ファイル
| ファイル | 説明 |
|---------|------|
| `boot.py` | USB CDC初期化（console用とdata用の2ポート） |
| `main.py` | メインプログラム（USB CDCでデータ受信、GPIO制御） |

### Windows側ファイル
| ファイル | 説明 |
|---------|------|
| `pico_serial_loader.py` | Intel Hexファイル転送スクリプト |
| `test_serial.py` | シリアル通信テストスクリプト |

### ドキュメント
- `README.md` - 本ドキュメント（プロトコル仕様を含む）

## セットアップ手順

### 1. 依存関係のインストール
```bash
pip install -r ../requirements.txt
```

### 2. PICOの準備
1. `boot.py`と`main.py`をPICOのルートディレクトリにコピー
2. PICOを再起動（USBケーブルを抜き差し）
3. 2つのシリアルポートが認識されることを確認

### 3. シリアルポートの確認

#### Windows
```cmd
# デバイスマネージャーで確認
devmgmt.msc

# コマンドラインで確認
python test_serial.py
```

#### Linux
```bash
# シリアルポートを確認
ls /dev/ttyACM*
# 通常は /dev/ttyACM0 (REPL) と /dev/ttyACM1 (Data)
```

通常、2つのポートが表示されます：
- **1つ目のポート**: REPL/デバッグ出力用
- **2つ目のポート**: データ通信用（自動検出される）

## 使用方法

### 基本的な使用
```bash
# Hexファイルを転送（ポート自動検出）
python pico_serial_loader.py <hexファイル>

# デバッグモードで実行
python pico_serial_loader.py -d <hexファイル>

# ポートを指定
python pico_serial_loader.py -p COM5 <hexファイル>
```

### テスト実行
```bash
# 1. シリアル通信テスト
python test_serial.py

# 2. サンプルHexファイルで転送テスト
python pico_serial_loader.py ../intel_hex_sample.hex -d
```

サンプルファイル（`intel_hex_sample.hex`）の内容：
- アドレス 0xC200-0xC23F: 64バイトのデータ
- アドレス 0x0000-0x0003: 4バイトのデータ
- 拡張アドレスレコード含む（下位8ビットのみ使用）

## コマンドラインオプション

```
usage: pico_serial_loader.py [-h] [-p PORT] [-b BAUDRATE] [-d] hexfile

positional arguments:
  hexfile               転送するIntel Hexファイル

optional arguments:
  -h, --help            ヘルプを表示
  -p PORT, --port PORT  シリアルポート（省略時は自動検出）
  -b BAUDRATE           ボーレート（デフォルト: 115200）
  -d, --debug           デバッグモード
```

## GPIO仕様

| GPIO | 機能 | 説明 |
|------|------|------|
| 0-7 | アドレスバス | 8ビットアドレス（LSBがGPIO0） |
| 8-15 | データバス | 8ビットデータ（LSBがGPIO8） |
| 16 | /WE信号 | Write Enable（アクティブLow） |

### タイミング
1. /WE信号をHigh（非アクティブ）に設定
2. アドレスとデータを設定
3. /WE信号をLow（アクティブ）に設定（10ms）
4. /WE信号をHigh（非アクティブ）に戻す
5. 次のデータまで10ms待機

## トラブルシューティング

### PICOが見つからない
- USBケーブルを確認（データ通信対応のケーブルか）
- boot.pyとmain.pyが正しくコピーされているか確認
- PICOを再起動（USBケーブルを抜き差し）

### シリアルポートが1つしか見えない
- boot.pyが実行されていない可能性があります
- PICOのファイルシステムにアクセスして、boot.pyの内容を確認してください

### 「USB CDC initialization failed」エラー
- MicroPythonのバージョンを確認（v1.19以降推奨）
- boot.pyの内容が正しいか確認
- PICOを完全にリセット（BOOTSELボタンを押しながら接続）

### デバッグ方法
1. REPL（1つ目のポート）に接続してデバッグ出力を確認
2. `test_serial.py`で基本的な通信を確認
3. `-d`オプションで詳細なログを表示

## 実装状態

実装完了：
- シリアル通信プロトコル（シンプルなテキストベース）
- PICO側スクリプト（USB CDC版）
- Windows側転送スクリプト
- 自動ポート検出
- エラーハンドリング
- デバッグ出力の分離（USB CDC使用）
- CRLF/LF両対応

## 通信プロトコル仕様

### 通信設定
- ボーレート: 115200 bps
- データビット: 8
- パリティ: なし
- ストップビット: 1
- フロー制御: なし

### コマンドフォーマット

#### 固定長コマンド（Ping、End）
```
<CMD>\n
```

- `CMD`: コマンドタイプ（1文字: P, E）

#### 可変長コマンド（Write）
```
W:<START_ADDRESS>:<LENGTH>:<DATA>\n
```

- `CMD`: コマンドタイプ（1文字: W）
- `START_ADDRESS`: 開始アドレス（16進数2桁、00-FF）
- `LENGTH`: データ長（16進数2桁、01-FF）
- `DATA`: データ（16進数、LENGTHバイト分）

### レスポンスフォーマット
```
<STATUS>:<MESSAGE>\n
```

### コマンド一覧

| コマンド | 説明 | フォーマット | レスポンス |
|---------|------|-------------|-----------|
| P | Ping（接続確認） | P\n | OK:READY |
| W | Write（データ書き込み） | W:ADDR:LEN:DATA\n | OK:WRITE |
| E | End（転送終了） | E\n | OK:END |

### エラーレスポンス

| エラー | メッセージ | 説明 |
|--------|-----------|------|
| ERR:FORMAT | フォーマットエラー | コマンドフォーマットが不正 |
| ERR:COMMAND | コマンドエラー | 不明なコマンド |
| ERR:LENGTH | 長さエラー | データ長が不正（0または255超） |

### 通信シーケンス例

```
# 基本的な転送シーケンス
1. PC → PICO: P\n              # Ping確認
2. PICO → PC: OK:READY\n       # 準備完了

3. PC → PICO: W:10:02:55AA\n   # アドレス0x10から2バイト書き込み
4. PICO → PC: OK:WRITE\n       # 書き込み完了

5. PC → PICO: E\n              # 転送終了
6. PICO → PC: OK:END\n         # 終了確認
```

### 実装上の注意点

1. **バッファサイズ**: 最大メッセージ長は520バイト程度
2. **最大行長**: 1024バイトを超える行は自動的に破棄
3. **改行コード処理**:
   - Windows側: 常にCRLF（\r\n）を送信
   - PICO側: CRLF（\r\n）とLF（\n）の両方を受け入れ
   - レスポンス: LF（\n）のみ
4. **文字エンコーディング**: UTF-8を使用