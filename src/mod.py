import json
import logging
import os
import zipfile
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

from init import RESOURCE_DIR, MODS_DIR
from prepare import extract_map_from_json, prepare_translation
from provider import provide_log_directory


def process_jar_file(jar_path):
    try:
        mod_name = get_mod_name_from_jar(jar_path)
        if mod_name is None:
            logging.warning(f"Mod name not found in: {jar_path}")
            return {}

        lang_path_in_jar = Path(f'assets/{mod_name}/lang/')
        ja_jp_path_in_jar = os.path.join(lang_path_in_jar, 'ja_jp.json')
        en_us_path_in_jar = os.path.join(lang_path_in_jar, 'en_us.json')
        ja_jp_path_in_jar_str = str(ja_jp_path_in_jar).replace('\\', '/')
        en_us_path_in_jar_str = str(en_us_path_in_jar).replace('\\', '/')

        logging.info(f"Processing mod: {mod_name} from {jar_path}")
        
        # 一時ディレクトリを作成
        temp_dir = os.path.join(provide_log_directory(), "temp_extract")
        os.makedirs(temp_dir, exist_ok=True)

        extracted_files = []
        try:
            with zipfile.ZipFile(jar_path, 'r') as zip_ref:
                if en_us_path_in_jar_str in zip_ref.namelist():
                    if extract_specific_file(jar_path, en_us_path_in_jar_str, temp_dir):
                        extracted_files.append(en_us_path_in_jar)
                if ja_jp_path_in_jar_str in zip_ref.namelist():
                    if extract_specific_file(jar_path, ja_jp_path_in_jar_str, temp_dir):
                        extracted_files.append(ja_jp_path_in_jar)
        except zipfile.BadZipFile as e:
            logging.error(f"Invalid JAR file: {jar_path} - {str(e)}")
            return {}

        # 優先順位: ja_jp.json > en_us.json
        for file in extracted_files:
            file_path = os.path.join(temp_dir, file)
            if os.path.exists(file_path):
                try:
                    result = extract_map_from_json(file_path)
                    if result:
                        return result
                except Exception as e:
                    logging.error(f"Error processing {file}: {str(e)}")

        logging.warning(f"No valid lang files found in: {jar_path}")
        return {}
    except Exception as e:
        logging.error(f"Unexpected error processing {jar_path}: {str(e)}")
        return {}

def translate_from_jar():
    # リソースディレクトリの準備
    os.makedirs(os.path.join(RESOURCE_DIR, 'assets', 'japanese', 'lang'), exist_ok=True)
    
    targets = {}
    jar_files = [f for f in os.listdir(MODS_DIR) if f.endswith('.jar')]
    
    if not jar_files:
        logging.warning(f"No JAR files found in {MODS_DIR}")
        return

    # pack.mcmetaの処理 (最初の有効なJARから取得)
    extracted_pack_mcmeta = False
    for jar in jar_files:
        if not extracted_pack_mcmeta:
            extracted_pack_mcmeta = extract_specific_file(
                os.path.join(MODS_DIR, jar),
                'pack.mcmeta',
                RESOURCE_DIR
            )
            if extracted_pack_mcmeta:
                update_resourcepack_description(
                    os.path.join(RESOURCE_DIR, 'pack.mcmeta'),
                    '日本語化パック'
                )
                break

    # 並列処理でJARファイルを処理
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(
                process_jar_file,
                os.path.join(MODS_DIR, jar)
            ): jar for jar in jar_files
        }
        
        # 進捗表示
        for future in tqdm(
            as_completed(futures),
            total=len(jar_files),
            desc="Processing MODs",
            unit="MOD"
        ):
            try:
                result = future.result()
                if result:
                    targets.update(result)
            except Exception as e:
                logging.error(f"Error processing {futures[future]}: {str(e)}")

    try:
        # 翻訳実行
        translated_map = prepare_translation(list(targets.values()))
        if not translated_map:
            logging.warning("No translations were generated")
            return

        # 翻訳済みと未翻訳を分類
        translated_targets = {
            json_key: translated_map[original]
            for json_key, original in targets.items()
            if original in translated_map
        }
        untranslated_items = {
            json_key: original
            for json_key, original in targets.items()
            if original not in translated_map
        }

        # 翻訳結果の保存
        output_file = os.path.join(RESOURCE_DIR, 'assets', 'japanese', 'lang', 'ja_jp.json')
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding="utf-8") as f:
            json.dump(
                dict(sorted(translated_targets.items())),
                f,
                ensure_ascii=False,
                indent=4
            )
        logging.info(f"Saved translations to {output_file}")

        # 未翻訳アイテムの記録
        if untranslated_items:
            error_directory = os.path.join(provide_log_directory(), 'error')
            os.makedirs(error_directory, exist_ok=True)
            
            error_file = os.path.join(error_directory, 'mod_ja_jp.json')
            with open(error_file, 'w', encoding="utf-8") as f:
                json.dump(
                    dict(sorted(untranslated_items.items())),
                    f,
                    ensure_ascii=False,
                    indent=4
                )
            logging.warning(f"Saved {len(untranslated_items)} untranslated items to {error_file}")

    except Exception as e:
        logging.error(f"Error processing translations: {str(e)}")
        raise


def update_resourcepack_description(file_path, new_description):
    # ファイルが存在するか確認
    if not os.path.exists(file_path):
        return

    with open(file_path, 'r', encoding='utf-8') as file:
        try:
            data = json.load(file)
        except json.JSONDecodeError as e:
            return

    # 'description'の'text'を新しい値に更新
    try:
        if 'pack' in data and 'description' in data['pack'] and 'text' in data['pack']['description']:
            data['pack']['description']['text'] = new_description
        else:
            return
    except Exception as e:
        return

    # 変更を加えたデータを同じファイルに書き戻す
    with open(file_path, 'w', encoding='utf-8') as file:
        try:
            json.dump(data, file, ensure_ascii=False, indent=2)  # JSONを整形して書き込み
        except Exception as e:
            return


def get_mod_name_from_jar(jar_path):
    with zipfile.ZipFile(jar_path, 'r') as zip_ref:
        asset_dirs_with_lang = set()
        for name in zip_ref.namelist():
            parts = name.split('/')
            if len(parts) > 3 and parts[0] == 'assets' and parts[2] == 'lang' and parts[1] != 'minecraft':
                asset_dirs_with_lang.add(parts[1])
        if asset_dirs_with_lang:
            return list(asset_dirs_with_lang)[0]
    return None


def extract_specific_file(zip_filepath, file_name, dest_dir):
    with zipfile.ZipFile(zip_filepath, 'r') as zip_ref:
        if file_name in zip_ref.namelist():
            zip_ref.extract(file_name, dest_dir)
            return True
        else:
            logging.info(f"The file {file_name} in {zip_filepath} was not found in the ZIP archive.")
    return False
