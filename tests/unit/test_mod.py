import pytest
import os
import zipfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import logging

from src.mod import (
    process_jar_file,
    get_mod_name_from_jar,
    extract_specific_file,
    translate_from_jar
)

# テスト用フィクスチャ
@pytest.fixture
def temp_dir(tmp_path):
    return tmp_path

@pytest.fixture
def mock_jar_with_lang(tmp_path):
    """言語ファイルを含むモックJARを作成"""
    jar_path = tmp_path / "test_mod.jar"
    with zipfile.ZipFile(jar_path, 'w') as z:
        # assets/testmod/lang/en_us.json を作成
        en_us_content = json.dumps({"item.test": "Test Item"})
        z.writestr("assets/testmod/lang/en_us.json", en_us_content)
        
        # assets/testmod/lang/ja_jp.json を作成
        ja_jp_content = json.dumps({"item.test": "テストアイテム"})
        z.writestr("assets/testmod/lang/ja_jp.json", ja_jp_content)
        
        # pack.mcmeta も追加
        z.writestr("pack.mcmeta", json.dumps({
            "pack": {
                "description": {"text": "Test Pack"},
                "pack_format": 1
            }
        }))
    return jar_path

@pytest.fixture
def mock_jar_no_lang(tmp_path):
    """言語ファイルを含まないモックJARを作成"""
    jar_path = tmp_path / "no_lang_mod.jar"
    with zipfile.ZipFile(jar_path, 'w') as z:
        z.writestr("META-INF/MANIFEST.MF", "Manifest-Version: 1.0")
    return jar_path

@pytest.fixture
def mock_logging():
    """ロギングのモック設定"""
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    return logger

# テストケース
class TestGetModNameFromJar:
    def test_valid_jar(self, mock_jar_with_lang):
        mod_name = get_mod_name_from_jar(str(mock_jar_with_lang))
        assert mod_name == "testmod"

    def test_invalid_jar(self, tmp_path):
        invalid_jar = tmp_path / "invalid.jar"
        invalid_jar.write_text("not a zip file")
        mod_name = get_mod_name_from_jar(str(invalid_jar))
        assert mod_name is None

    def test_no_lang_jar(self, mock_jar_no_lang):
        mod_name = get_mod_name_from_jar(str(mock_jar_no_lang))
        assert mod_name is None

class TestProcessJarFile:
    def test_process_jar_with_both_lang_files(self, mock_jar_with_lang, temp_dir):
        with patch('src.mod.provide_log_directory', return_value=str(temp_dir)):
            result = process_jar_file(str(mock_jar_with_lang))
            assert "item.test" in result
            assert len(result) > 0

    def test_process_jar_with_only_en_us(self, tmp_path):
        jar_path = tmp_path / "en_only.jar"
        with zipfile.ZipFile(jar_path, 'w') as z:
            z.writestr("assets/testmod/lang/en_us.json", json.dumps({"item.test": "Test"}))
        
        with patch('src.mod.provide_log_directory', return_value=str(tmp_path)):
            result = process_jar_file(str(jar_path))
            assert "item.test" in result

    def test_process_jar_with_invalid_json(self, tmp_path):
        jar_path = tmp_path / "invalid_json.jar"
        with zipfile.ZipFile(jar_path, 'w') as z:
            z.writestr("assets/testmod/lang/en_us.json", "invalid json")
        
        with patch('src.mod.provide_log_directory', return_value=str(tmp_path)):
            result = process_jar_file(str(jar_path))
            assert result == {}

    def test_process_jar_with_bad_zip(self, tmp_path):
        bad_jar = tmp_path / "bad.zip"
        bad_jar.write_text("not a zip file")
        
        with patch('src.mod.provide_log_directory', return_value=str(tmp_path)):
            result = process_jar_file(str(bad_jar))
            assert result == {}

class TestExtractSpecificFile:
    def test_extract_existing_file(self, mock_jar_with_lang, temp_dir):
        result = extract_specific_file(
            str(mock_jar_with_lang),
            "assets/testmod/lang/en_us.json",
            str(temp_dir)
        )
        assert result is True
        assert (temp_dir / "assets/testmod/lang/en_us.json").exists()

    def test_extract_non_existing_file(self, mock_jar_with_lang, temp_dir):
        result = extract_specific_file(
            str(mock_jar_with_lang),
            "non_existing_file.json",
            str(temp_dir)
        )
        assert result is False

class TestTranslateFromJar:
    @patch('src.mod.MODS_DIR', 'test_mods_dir')
    @patch('src.mod.RESOURCE_DIR', 'test_resource_dir')
    @patch('src.mod.prepare_translation')
    @patch('os.listdir')
    @patch('os.makedirs')
    def test_translate_from_jar_success(
        self, mock_makedirs, mock_listdir, mock_prepare
    ):
        # モック設定
        mock_listdir.return_value = ['test1.jar', 'test2.jar']
        mock_prepare.return_value = {'test': 'テスト'}
        
        # モックJAR処理結果
        with patch('src.mod.process_jar_file') as mock_process:
            mock_process.side_effect = [
                {'key1': 'value1'},
                {'key2': 'value2'}
            ]
            
            # テスト実行
            translate_from_jar()
            
            # 検証
            assert mock_process.call_count == 2
            mock_prepare.assert_called_once_with(['value1', 'value2'])
            assert mock_makedirs.call_count >= 1

    @patch('src.mod.MODS_DIR', 'empty_dir')
    @patch('os.listdir')
    def test_translate_from_jar_no_files(self, mock_listdir):
        mock_listdir.return_value = []
        with patch('logging.warning') as mock_warning:
            translate_from_jar()
            mock_warning.assert_called_once()