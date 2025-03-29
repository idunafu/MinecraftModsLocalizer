import itertools
import json
import logging
import os
import re

from init import MAX_ATTEMPTS
from chatgpt import translate_with_chatgpt
from provider import provide_chunk_size, provide_request_interval


def extract_map_from_lang(filepath):
    collected_map = {}
    with open(filepath, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()  # 余分な空白や改行を削除
            if line and not line.startswith('#'):
                key, value = line.split('=', 1)
                collected_map[key.strip()] = value.strip()
    return collected_map


def extract_map_from_json(file_path):
    collected_map = {}

    if os.path.exists(file_path):
        logging.info(f"Extract keys in en_us.json(or ja_jp.json) in {file_path}")
        try:
            with open(file_path, 'r', encoding="utf-8") as f:
                content = json.load(f)

            # 値が英語でコメント以外のキーのみを保存します。
            for key, value in content.items():
                if not key.startswith("_comment") and isinstance(value, str) and not re.search('[\u3040-\u30FF\u3400-\u4DBF\u4E00-\u9FFF]', value):
                    collected_map[key] = value

        except json.JSONDecodeError:
            logging.info(
                f"Failed to load or process JSON from {file_path}. Skipping this mod for translation. Please check the file for syntax errors.")
    else:
        logging.info(f"Could not find {file_path}. Skipping this mod for translation.")

    return collected_map


def split_list(big_list):
    # 分割されたリストを格納するリスト
    list_of_chunks = []

    # 元のリストの要素を順に処理し、指定のサイズごとに分割
    for i in range(0, len(big_list), provide_chunk_size()):
        # 現在の位置から最大要素数だけを新しいリストに切り出し
        chunk = big_list[i:i + provide_chunk_size()]
        # 新しいリストをリストに追加
        list_of_chunks.append(chunk)

    return list_of_chunks


def create_map_with_none_filling(split_target, translated_split_target):
    # 辞書を作成し、zip_longestを使用してリストの長さが異なる場合にNoneで埋める
    result_map = {}
    for key, value in itertools.zip_longest(split_target, translated_split_target):
        # valueが空白文字の場合、空文字列に置換する（Noneは置換しない）
        if value == '':
            value = None
        result_map[key] = value

    return result_map


from typing import Dict, List, Any, Union

def create_mod_aware_chunks(mod_data: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    MODごとにテキストをチャンク分割し、MOD区切りマーカーを追加する
    
    Args:
        mod_data: {
            "mod_name": {
                "jar_path": str,
                "texts": List[str],
                "original_keys": List[str]
            }
        }
    
    Returns:
        List of chunks, each either:
        - {"mod_name": str, "texts": List[str], "is_full_mod": bool} (単一MODチャンク)
        - {"mod_names": List[str], "texts": List[str], "headers": List[str]} (複数MODチャンク)
    """
    chunks: List[Dict[str, Any]] = []
    current_chunk: Dict[str, Any] = {}  # 空の辞書で初期化
    current_chunk_size = 0
    chunk_size_limit = provide_chunk_size()
    has_current_chunk = False  # 有効なデータがあるか追跡
    
    for mod_name, data in mod_data.items():
        mod_texts = data["texts"]
        mod_header = f"\n--- MOD: {mod_name} ---\n"
        mod_header_size = 1  # ヘッダーは1行としてカウント
        
        # MODが大きい場合（単独でチャンクサイズを超える場合）
        if len(mod_texts) > chunk_size_limit:
            # MODを複数チャンクに分割
            for i in range(0, len(mod_texts), chunk_size_limit):
                chunk = mod_texts[i:i + chunk_size_limit]
                chunk_data = {
                    "mod_name": mod_name,
                    "texts": chunk,
                    "is_full_mod": False
                }
                chunks.append(chunk_data)
        else:
            # MODが小さい場合、現在のチャンクに追加可能かチェック
            if current_chunk and current_chunk_size + len(mod_texts) + mod_header_size > chunk_size_limit:
                chunks.append(current_chunk)
                current_chunk = None
                current_chunk_size = 0
            
            # MODを現在のチャンクに追加
            if not current_chunk:  # 新しいチャンクの場合
                current_chunk = {
                    "mod_names": [mod_name],
                    "texts": mod_texts,
                    "headers": [mod_header]
                }
                current_chunk_size = len(mod_texts) + mod_header_size
            else:  # 既存のチャンクに追加
                current_chunk["mod_names"].append(mod_name)
                current_chunk["texts"].extend(mod_texts)
                current_chunk["headers"].append(mod_header)
                current_chunk_size += len(mod_texts) + mod_header_size
    
    # 最後のチャンクを追加
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks

from typing import Dict, List, Any

def prepare_translation(mod_data: Dict[str, Dict[str, Any]]) -> Dict[str, str]:
    """
    MODごとのデータを受け取り、翻訳を実行する
    
    Args:
        mod_data: {
            "mod_name": {
                "jar_path": str,
                "texts": List[str],
                "original_keys": List[str]
            }
        }
    
    Returns:
        翻訳結果のマップ {原文: 訳文}
    """
    chunks = create_mod_aware_chunks(mod_data)
    result_map: Dict[str, str] = {}
    timeout = 60 * 3  # 3分のタイムアウト
    
    # リクエスト間隔の情報をログに出力
    request_interval = provide_request_interval()
    if request_interval > 0:
        logging.info(f"Using request interval: {request_interval} seconds between API requests")

    total_chunks = len(chunks)
    total_mods = len(mod_data)
    logging.info(f"Total MODs to translate: {total_mods}")
    logging.info(f"Total chunks to process: {total_chunks}")

    for index, chunk in enumerate(chunks, 1):
        logging.info(f"Processing chunk {index}/{total_chunks}...")
        
        # チャンクのテキストを準備 (MODヘッダーを追加)
        if isinstance(chunk.get("mod_names"), list):  # 複数MODがまとめられたチャンク
            texts: List[str] = []
            mod_sections: List[Dict[str, Any]] = []
            
            for mod_name, mod_texts, header in zip(
                chunk["mod_names"],
                chunk["texts"],
                chunk["headers"]
            ):
                texts.append(header)
                texts.extend(mod_texts)
                mod_sections.append({
                    "mod_name": mod_name,
                    "texts": mod_texts,
                    "header": header
                })
        else:  # 単一MODのチャンク
            texts = [f"\n--- MOD: {chunk['mod_name']} ---\n"] + chunk["texts"]
            mod_sections = [{
                "mod_name": chunk["mod_name"],
                "texts": chunk["texts"],
                "header": f"\n--- MOD: {chunk['mod_name']} ---\n"
            }]

        attempts = 0
        while attempts < MAX_ATTEMPTS:
            # 翻訳実行
            translated_texts = translate_with_chatgpt(texts, timeout)
            
            if len(texts) != len(translated_texts):
                attempts += 1
                if attempts == MAX_ATTEMPTS:
                    logging.error(f"Failed to translate chunk {index}/{total_chunks} after {MAX_ATTEMPTS} attempts")
                continue
                
            # MODセクションごとに結果を処理
            current_pos = 0
            for section in mod_sections:
                # ヘッダー分をスキップ
                current_pos += 1
                # 翻訳結果を取得
                section_translated = translated_texts[current_pos:current_pos + len(section["texts"])]
                # 元のテキストと翻訳結果をマッピング
                for orig, trans in zip(section["texts"], section_translated):
                    result_map[orig] = trans
                current_pos += len(section["texts"])
            
            break  # 成功したらループを抜ける

    logging.info("Translation completed!")
    return result_map
