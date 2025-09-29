# Intel Hex Loader

Intel Hexファイルを読み込み、解析、変換するためのPythonライブラリです。

## 機能

- Intel Hexフォーマットのファイルの読み込み
- データの検証（チェックサム、アドレス範囲）
- バイナリデータへの変換
- メモリマップの生成
- 拡張アドレッシング（セグメント/リニア）のサポート
- 統計情報の取得

## インストール

```bash
pip install -r requirements.txt
```

## 基本的な使用方法

### ファイルの読み込み

```python
from intel_hex_loader import IntelHexLoader

# ローダーのインスタンスを作成
loader = IntelHexLoader()

# Hexファイルを読み込み
loader.load_file('firmware.hex')

# または文字列から読み込み
hex_string = """
:020000040000FA
:10000000214601360121470136007EFE09D2194002
:00000001FF
"""
loader.load_string(hex_string)
```

### メモリマップの確認

```python
# メモリマップを表示
loader.print_memory_map()

# プログラムでメモリマップを取得
regions = loader.get_memory_map()
for start, end in regions:
    size = end - start + 1
    print(f"領域: 0x{start:08X} - 0x{end:08X} ({size} バイト)")
```

### バイナリデータへの変換

```python
# 全体をバイナリに変換（デフォルトのフィルバイト: 0xFF）
binary_data = loader.to_binary()

# カスタムフィルバイトを使用
binary_data = loader.to_binary(fill_byte=0x00)

# 特定のアドレス範囲のみを抽出
binary_data = loader.to_binary(start_address=0x1000, end_address=0x2000)
```

### 統計情報の取得

```python
# 統計情報を取得
stats = loader.get_statistics()
print(f"総レコード数: {stats['total_records']}")
print(f"データレコード数: {stats['data_records']}")
print(f"総バイト数: {stats['total_bytes']}")
print(f"メモリ領域数: {stats['memory_regions']}")

# レコードタイプ別の集計
for record_type, count in stats['record_types'].items():
    print(f"{record_type}: {count}")
```

### エラーハンドリング

```python
try:
    loader.load_file('firmware.hex')
except FileNotFoundError:
    print("ファイルが見つかりません")
except ValueError as e:
    print(f"フォーマットエラー: {e}")
```

### 高度な使用例

```python
# レコードへの直接アクセス
for record in loader.records:
    print(f"タイプ: {record.record_type.name}")
    print(f"アドレス: 0x{record.address:04X}")
    print(f"データ長: {record.length}")
    if record.data:
        print(f"データ: {record.data.hex()}")

# メモリへの直接アクセス
for address, value in loader.memory.items():
    print(f"0x{address:08X}: 0x{value:02X}")

# エントリポイントの確認
if loader.start_address is not None:
    print(f"エントリポイント: 0x{loader.start_address:08X}")
```

## 実用的な例

### ファームウェアの検証

```python
def verify_firmware(hex_file, expected_size=None, expected_checksum=None):
    """ファームウェアファイルを検証"""
    loader = IntelHexLoader()
    
    try:
        loader.load_file(hex_file)
        
        # サイズの確認
        actual_size = loader.get_statistics()['total_bytes']
        if expected_size and actual_size != expected_size:
            return False, f"サイズが一致しません: 期待値={expected_size}, 実際={actual_size}"
        
        # バイナリデータのチェックサム計算（簡易版）
        binary = loader.to_binary()
        actual_checksum = sum(binary) & 0xFFFF
        if expected_checksum and actual_checksum != expected_checksum:
            return False, f"チェックサムが一致しません"
        
        return True, "検証成功"
        
    except Exception as e:
        return False, f"エラー: {e}"
```

### バイナリファイルへの変換

```python
def hex_to_bin(hex_file, bin_file, fill_byte=0xFF):
    """Intel Hexファイルをバイナリファイルへ変換"""
    loader = IntelHexLoader()
    loader.load_file(hex_file)
    
    # バイナリデータを取得
    binary_data = loader.to_binary(fill_byte=fill_byte)
    
    # ファイルに書き込み
    with open(bin_file, 'wb') as f:
        f.write(binary_data)
    
    print(f"変換完了: {len(binary_data)} バイト")
```

### 複数ファイルの結合

```python
def merge_hex_files(file_list, output_file):
    """複数のIntel Hexファイルを結合"""
    merged_loader = IntelHexLoader()
    
    for hex_file in file_list:
        temp_loader = IntelHexLoader()
        temp_loader.load_file(hex_file)
        
        # メモリデータを結合
        for address, value in temp_loader.memory.items():
            if address in merged_loader.memory:
                print(f"警告: アドレス 0x{address:08X} が重複しています")
            merged_loader.memory[address] = value
    
    # 結合したデータをIntel Hex形式で出力（簡易版）
    # 実際の実装では適切なIntel Hex形式での出力が必要
    binary = merged_loader.to_binary()
    print(f"結合完了: {len(binary)} バイト")
```

### メモリ使用量の分析

```python
def analyze_memory_usage(hex_file):
    """メモリ使用量を分析"""
    loader = IntelHexLoader()
    loader.load_file(hex_file)
    
    regions = loader.get_memory_map()
    total_used = 0
    
    print("メモリ使用状況:")
    print("-" * 60)
    
    for start, end in regions:
        size = end - start + 1
        total_used += size
        
        # メモリ領域の種類を判定（仮想的な例）
        if start < 0x1000:
            region_type = "ブートローダー"
        elif start < 0x10000:
            region_type = "プログラム領域"
        elif start < 0x20000:
            region_type = "データ領域"
        else:
            region_type = "拡張領域"
        
        print(f"{region_type:15} : 0x{start:08X} - 0x{end:08X} ({size:6} バイト)")
    
    print("-" * 60)
    print(f"総使用量: {total_used} バイト")
```

## Intel Hexフォーマットについて

Intel Hexは、バイナリデータをテキスト形式で表現するフォーマットです。各行は以下の構造を持ちます：

```
:LLAAAATT[DD...]CC
```

- `:` : 開始コード
- `LL` : データ長（バイト数）
- `AAAA` : アドレス（16ビット）
- `TT` : レコードタイプ
- `DD` : データ（可変長）
- `CC` : チェックサム

### レコードタイプ

- `00` : データレコード
- `01` : ファイル終了レコード
- `02` : 拡張セグメントアドレスレコード
- `03` : スタートセグメントアドレスレコード
- `04` : 拡張リニアアドレスレコード
- `05` : スタートリニアアドレスレコード

## トラブルシューティング

### よくあるエラーと対処法

#### チェックサムエラー
```
ValueError: 行 X: チェックサムエラー (期待値: XX, 実際: YY)
```
**原因**: Intel Hexファイルの該当行でチェックサムが正しくない  
**対処**: ファイルが破損していないか確認。テキストエディタで編集した場合は、各行のチェックサムを再計算する必要があります。

#### データ長エラー
```
ValueError: 行 X: データ長が不正です
```
**原因**: 宣言されたデータ長と実際のデータバイト数が一致しない  
**対処**: 該当行のLLフィールド（データ長）が正しいか確認

#### 無効な文字エラー
```
ValueError: 行 X: 無効な文字が含まれています
```
**原因**: 16進数以外の文字が含まれている  
**対処**: 該当行に0-9, A-F以外の文字がないか確認

### パフォーマンスに関する注意事項

- **大きなファイル**: 数MBを超えるIntel Hexファイルの場合、メモリ使用量に注意
- **スパースなデータ**: アドレスが大きく離れたデータの場合、`to_binary()`でフィルバイトが大量に生成される可能性があります
- **メモリ効率**: 必要に応じて`start_address`と`end_address`を指定して、特定の領域のみを抽出

### 制限事項

- 32ビットアドレッシングまでサポート（拡張リニアアドレスレコードによる）
- Intel Hex形式での書き出し機能は含まれていません（読み込み専用）
- カスタムレコードタイプはサポートしていません

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。
