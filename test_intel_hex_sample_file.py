#!/usr/bin/env python3
"""
intel_hex_sample.hexファイルを使用したIntel Hexローダーのテスト
"""

from intel_hex_loader import IntelHexLoader

print("=== intel_hex_sample.hex のテスト ===\n")

# ローダーのインスタンスを作成
loader = IntelHexLoader()

try:
    # Hexファイルを読み込み
    print("ファイルを読み込み中...")
    loader.load_file('intel_hex_sample.hex')
    print("[OK] ファイルの読み込みに成功しました\n")
    
    # 統計情報を表示
    print("統計情報:")
    stats = loader.get_statistics()
    print(f"  総レコード数: {stats['total_records']}")
    print(f"  データレコード数: {stats['data_records']}")
    print(f"  総バイト数: {stats['total_bytes']}")
    print(f"  メモリ領域数: {stats['memory_regions']}")
    print(f"  レコードタイプ別:")
    for record_type, count in stats['record_types'].items():
        print(f"    {record_type}: {count}")
    
    # メモリマップを表示
    print("\nメモリマップ:")
    loader.print_memory_map()
    
    # 各レコードの詳細を表示
    print("\n各レコードの詳細:")
    for i, record in enumerate(loader.records, 1):
        print(f"  レコード {i}:")
        print(f"    タイプ: {record.record_type.name} ({record.record_type:02X})")
        print(f"    アドレス: 0x{record.address:04X}")
        print(f"    データ長: {record.length} バイト")
        if record.data:
            data_hex = ' '.join(f'{b:02X}' for b in record.data[:8])
            if len(record.data) > 8:
                data_hex += ' ...'
            print(f"    データ: {data_hex}")
    
    # バイナリデータに変換
    print("\nバイナリデータへの変換:")
    binary_data = loader.to_binary()
    print(f"  バイナリサイズ: {len(binary_data)} バイト")
    
    # メモリ領域ごとの内容を表示
    print("\nメモリ領域の内容:")
    regions = loader.get_memory_map()
    for start, end in regions:
        size = end - start + 1
        print(f"\n  領域 0x{start:08X} - 0x{end:08X} ({size} バイト):")
        
        # 最初の32バイトを16進ダンプ形式で表示
        region_start_in_binary = start - min(loader.memory.keys())
        region_data = binary_data[region_start_in_binary:region_start_in_binary + min(32, size)]
        
        for i in range(0, len(region_data), 16):
            hex_str = ' '.join(f'{b:02X}' for b in region_data[i:i+16])
            ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in region_data[i:i+16])
            print(f"    {start + i:08X}: {hex_str:<48} |{ascii_str}|")
        
        if size > 32:
            print(f"    ... ({size - 32} バイト省略)")
    
    # エントリポイントの確認
    if loader.start_address is not None:
        print(f"\nエントリポイント: 0x{loader.start_address:08X}")
    else:
        print("\nエントリポイント: なし")
    
    print("\n[OK] すべてのテストが正常に完了しました")
    
except Exception as e:
    print(f"\n[ERROR] エラーが発生しました: {e}")
    import traceback
    traceback.print_exc()
