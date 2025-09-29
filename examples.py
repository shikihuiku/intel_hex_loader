#!/usr/bin/env python3
"""
Intel Hex Loaderの使用例
"""

from intel_hex_loader import IntelHexLoader


def example_basic_usage():
    """基本的な使用例"""
    print("=== 基本的な使用例 ===\n")
    
    # サンプルのIntel Hexデータ
    sample_hex = """
:020000040000FA
:10000000214601360121470136007EFE09D2194002
:100010002146017E17C20001FF5F16002148011929
:10002000194E79234623965778239EDA3F01B2CAA8
:100030003F0156702B5E712B722B732146013421C8
:00000001FF
"""
    
    # ローダーのインスタンスを作成
    loader = IntelHexLoader()
    
    # 文字列から読み込み
    loader.load_string(sample_hex)
    
    # メモリマップを表示
    loader.print_memory_map()
    
    # 統計情報を表示
    print("\n統計情報:")
    stats = loader.get_statistics()
    for key, value in stats.items():
        if key != 'record_types':
            print(f"  {key}: {value}")
    

def example_binary_conversion():
    """バイナリ変換の例"""
    print("\n\n=== バイナリ変換の例 ===\n")
    
    # 簡単なデータ
    hex_data = """
:10000000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF00
:1000100000112233445566778899AABBCCDDEEFFE8
:00000001FF
"""
    
    loader = IntelHexLoader()
    loader.load_string(hex_data)
    
    # バイナリデータに変換
    binary = loader.to_binary()
    print(f"バイナリデータサイズ: {len(binary)} bytes")
    
    # 最初の32バイトを16進ダンプ形式で表示
    print("\n16進ダンプ:")
    for i in range(0, min(32, len(binary)), 16):
        hex_str = ' '.join(f'{b:02X}' for b in binary[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in binary[i:i+16])
        print(f"{i:08X}: {hex_str:<48} |{ascii_str}|")
        

def example_extended_addressing():
    """拡張アドレッシングの例"""
    print("\n\n=== 拡張アドレッシングの例 ===\n")
    
    # 拡張リニアアドレスを使用したデータ
    hex_data = """
:020000040800F2
:10000000214601360121470136007EFE09D2194002
:020000041000EA
:10000000AABBCCDDEEFF00112233445566778899F8
:00000001FF
"""
    
    loader = IntelHexLoader()
    loader.load_string(hex_data)
    
    print("メモリマップ（拡張アドレス使用）:")
    regions = loader.get_memory_map()
    for start, end in regions:
        size = end - start + 1
        print(f"  0x{start:08X} - 0x{end:08X} ({size} bytes)")
        

def example_error_handling():
    """エラーハンドリングの例"""
    print("\n\n=== エラーハンドリングの例 ===\n")
    
    # 不正なデータの例
    invalid_data_examples = [
        ("開始文字なし", "10000000214601360121470136007EFE09D21940F1"),
        ("無効な文字", ":10000000GGGGGG"),
        ("チェックサムエラー", ":10000000214601360121470136007EFE09D21940FF"),
        ("短すぎる行", ":1000"),
    ]
    
    loader = IntelHexLoader()
    
    for description, hex_data in invalid_data_examples:
        try:
            loader.load_string(hex_data)
            print(f"{description}: エラーが検出されませんでした（異常）")
        except ValueError as e:
            print(f"{description}: {e}")
            

def example_custom_fill_byte():
    """カスタムフィルバイトの例"""
    print("\n\n=== カスタムフィルバイトの例 ===\n")
    
    # 離れたアドレスにデータがある場合
    hex_data = """
:04000000DEADBEEFC4
:04100000CAFEBABEAC
:00000001FF
"""
    
    loader = IntelHexLoader()
    loader.load_string(hex_data)
    
    # フィルバイトを0x00で埋める
    binary_00 = loader.to_binary(fill_byte=0x00, start_address=0x0000, end_address=0x1003)
    
    # フィルバイトを0xFFで埋める
    binary_ff = loader.to_binary(fill_byte=0xFF, start_address=0x0000, end_address=0x1003)
    
    print(f"0x00でフィル: 最初の8バイト = {' '.join(f'{b:02X}' for b in binary_00[:8])}")
    print(f"0xFFでフィル: 最初の8バイト = {' '.join(f'{b:02X}' for b in binary_ff[:8])}")
    

def example_file_operations():
    """ファイル操作の例"""
    print("\n\n=== ファイル操作の例 ===\n")
    
    # サンプルファイルを作成
    sample_filename = "sample.hex"
    
    with open(sample_filename, 'w') as f:
        f.write(":020000040000FA\n")
        f.write(":10000000214601360121470136007EFE09D2194002\n")
        f.write(":10001000194E79234623965778239EDA3F01B2CAB8\n")
        f.write(":04000005000000CD2A\n")
        f.write(":00000001FF\n")
    
    # ファイルから読み込み
    loader = IntelHexLoader()
    try:
        loader.load_file(sample_filename)
        print(f"ファイル '{sample_filename}' を正常に読み込みました")
        print(f"レコード数: {len(loader.records)}")
        print(f"データサイズ: {len(loader.memory)} bytes")
        
        if loader.start_address is not None:
            print(f"エントリポイント: 0x{loader.start_address:08X}")
            
    except FileNotFoundError as e:
        print(f"エラー: {e}")
    finally:
        # サンプルファイルを削除
        import os
        if os.path.exists(sample_filename):
            os.remove(sample_filename)
            print(f"\nサンプルファイル '{sample_filename}' を削除しました")


if __name__ == "__main__":
    # すべての例を実行
    example_basic_usage()
    example_binary_conversion()
    example_extended_addressing()
    example_error_handling()
    example_custom_fill_byte()
    example_file_operations()
