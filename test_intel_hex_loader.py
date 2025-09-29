#!/usr/bin/env python3
"""
Intel Hex Loaderのテストスクリプト
"""

import unittest
import tempfile
import os
from intel_hex_loader import IntelHexLoader, RecordType, HexRecord


class TestIntelHexLoader(unittest.TestCase):
    """Intel Hex Loaderのテストクラス"""
    
    def setUp(self):
        """各テストの前に実行される準備処理"""
        self.loader = IntelHexLoader()
        
    def test_parse_simple_data_record(self):
        """シンプルなデータレコードの解析テスト"""
        hex_line = ":10000000214601360121470136007EFE09D2194002"
        self.loader.load_string(hex_line + "\n:00000001FF")
        
        # レコード数の確認
        self.assertEqual(len(self.loader.records), 2)
        
        # 最初のレコードの確認
        record = self.loader.records[0]
        self.assertEqual(record.length, 0x10)
        self.assertEqual(record.address, 0x0000)
        self.assertEqual(record.record_type, RecordType.DATA)
        self.assertEqual(len(record.data), 16)
        
    def test_checksum_validation(self):
        """チェックサムの検証テスト"""
        # 不正なチェックサムを持つ行
        invalid_hex = ":10000000214601360121470136007EFE09D21940FF"  # 最後をFFに変更（正しいチェックサムは02）
        
        with self.assertRaises(ValueError) as context:
            self.loader.load_string(invalid_hex)
        self.assertIn("チェックサムエラー", str(context.exception))
        
    def test_extended_linear_address(self):
        """拡張リニアアドレスレコードのテスト"""
        hex_data = """
:020000040800F2
:10000000214601360121470136007EFE09D2194002
:00000001FF
"""
        self.loader.load_string(hex_data)
        
        # メモリアドレスの確認（0x0800 << 16 = 0x08000000）
        expected_base = 0x08000000
        self.assertIn(expected_base, self.loader.memory)
        
    def test_memory_map(self):
        """メモリマップのテスト"""
        hex_data = """
:10000000214601360121470136007EFE09D2194002
:10002000194E79234623965778239EDA3F01B2CAA8
:00000001FF
"""
        self.loader.load_string(hex_data)
        
        memory_map = self.loader.get_memory_map()
        self.assertEqual(len(memory_map), 2)  # 2つの不連続な領域
        self.assertEqual(memory_map[0], (0x0000, 0x000F))
        self.assertEqual(memory_map[1], (0x0020, 0x002F))
        
    def test_to_binary_with_fill(self):
        """バイナリ変換（フィル付き）のテスト"""
        hex_data = """
:04000000AABBCCDDEE
:040010001122334442
:00000001FF
"""
        self.loader.load_string(hex_data)
        
        # 0x00から0x13までのバイナリを取得（フィルバイト: 0xFF）
        binary = self.loader.to_binary(fill_byte=0xFF, start_address=0x00, end_address=0x13)
        
        # 期待される結果を確認
        expected = bytes([
            0xAA, 0xBB, 0xCC, 0xDD,  # 0x00-0x03: データ
            0xFF, 0xFF, 0xFF, 0xFF,  # 0x04-0x07: フィル
            0xFF, 0xFF, 0xFF, 0xFF,  # 0x08-0x0B: フィル
            0xFF, 0xFF, 0xFF, 0xFF,  # 0x0C-0x0F: フィル
            0x11, 0x22, 0x33, 0x44   # 0x10-0x13: データ
        ])
        self.assertEqual(binary, expected)
        
    def test_invalid_format(self):
        """不正なフォーマットのテスト"""
        # 開始文字なし
        with self.assertRaises(ValueError) as context:
            self.loader.load_string("10000000214601360121470136007EFE09D21940F1")
        self.assertIn("開始文字", str(context.exception))
        
        # 無効な文字
        with self.assertRaises(ValueError) as context:
            self.loader.load_string(":10000000GGGGGG")
        self.assertIn("無効な文字", str(context.exception))
        
    def test_file_loading(self):
        """ファイル読み込みのテスト"""
        # 一時ファイルを作成
        with tempfile.NamedTemporaryFile(mode='w', suffix='.hex', delete=False) as f:
            f.write(":10000000214601360121470136007EFE09D2194002\n")
            f.write(":00000001FF\n")
            temp_filename = f.name
            
        try:
            # ファイルを読み込み
            self.loader.load_file(temp_filename)
            self.assertEqual(len(self.loader.records), 2)
            self.assertEqual(len(self.loader.memory), 16)
        finally:
            # 一時ファイルを削除
            os.unlink(temp_filename)
            
    def test_start_linear_address(self):
        """スタートリニアアドレスレコードのテスト"""
        hex_data = """
:04000005000000CD2A
:00000001FF
"""
        self.loader.load_string(hex_data)
        self.assertEqual(self.loader.start_address, 0x000000CD)
        
    def test_statistics(self):
        """統計情報のテスト"""
        hex_data = """
:020000040000FA
:10000000214601360121470136007EFE09D2194002
:10001000194E79234623965778239EDA3F01B2CAB8
:04000005000000CD2A
:00000001FF
"""
        self.loader.load_string(hex_data)
        
        stats = self.loader.get_statistics()
        self.assertEqual(stats['total_records'], 5)
        self.assertEqual(stats['data_records'], 2)
        self.assertEqual(stats['total_bytes'], 32)
        self.assertEqual(stats['memory_regions'], 1)
        

class TestChecksumCalculation(unittest.TestCase):
    """チェックサム計算のテストクラス"""
    
    def test_checksum_calculation(self):
        """チェックサム計算の詳細テスト"""
        loader = IntelHexLoader()
        
        # 既知のデータでチェックサムを計算
        # :10000000214601360121470136007EFE09D2194002
        length = 0x10
        address = 0x0000
        record_type = RecordType.DATA
        data = bytes([0x21, 0x46, 0x01, 0x36, 0x01, 0x21, 0x47, 0x01,
                      0x36, 0x00, 0x7E, 0xFE, 0x09, 0xD2, 0x19, 0x40])
        
        checksum = loader._calculate_checksum(length, address, record_type, data)
        self.assertEqual(checksum, 0x02)


if __name__ == '__main__':
    # テストを実行
    unittest.main(verbosity=2)
