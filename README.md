# MinecraftModsLocalizer-fork

## 概要

**MinecraftModsLocalizer-fork**は、ChatGPT等のLLMを使用してMinecraftの以下を日本語に翻訳するツールです：

- Mod本体
- FTBQuests/BetterQuestingのクエスト
- Patchouliのガイドブック

**主な特徴**:

- OpenAI互換API(Geminiなど)対応
- Nuitkaビルドによる高速化
- チャンク処理による効率的な翻訳
- リソースパック自動生成

## fork版の差異

- uvを開発環境に採用
- OpenAI互換API対応
- Nuitkaでビルドし高速化
- UIレイアウト変更
- デフォルト翻訳プロンプト最適化
- MOD区切りを考慮したチャンク処理
- その他リファクタリング

## インストール

### 要件

- OpenAI APIキー

### 手順

1. 実行ファイルをMinecraftメインディレクトリに配置
2. 必要なディレクトリ構造例：

   ```
   Minecraftディレクトリ/
   │
   ├── minecraft-mods-localizer.exe
   ├── config/
   ├── kubejs/
   ├── mods/
   └── resourcepacks/
   ```

## 使用方法

1. OpenAI APIキーを取得
2. ソフトウェアを起動
3. 翻訳対象を選択
4. パラメータを設定:
   - **Chunk Size**: 翻訳精度と速度のバランス調整
   - **Model**: デフォルトモデル(GPT-4o mini)
   - **Prompt**: 上級者向けカスタマイズ可能

**推奨設定**:

- 単体Mod/クエスト: Chunk Size = 1
- ModPack一括翻訳: Chunk Size = 100

## 出力ファイル

| 翻訳対象 | 出力先 |
|---------|--------|
| Mod本体 | `resourcepacks/japanese` |
| Quests | `kubejs/assets/kubejs/lang/ja_jp.json` または `config/ftbquests/quests/chapters/*.snbt` |
| Patchouli | `{mod.jar}/assets/{mod_name}/patchouli_books/{guide_name}/ja_jp` |

## トラブルシューティング

### よくある問題

1. **リソースパックが表示されない**
   - `pack.mcmeta`のインデントを確認

2. **翻訳失敗時の対応**
   - 手動で編集可能:
     - Mod: `logs/localizer/error` → `resourcepacks/japanese/lang/ja_jp.json`
     - Quest: `logs/localizer/error` → `/kubejs/assets/kubejs/lang/ja_jp.json`

3. **Quest翻訳の注意点**
   - SNBTファイル直接編集時はログが残らない

## 技術詳細

### 内部処理フロー

1. **Mod翻訳**:
   - JARから`en_us.json`を抽出
   - 日本語化してリソースパック生成

2. **Quest翻訳**:
   - `en_us.json`存在確認
   - 存在しない場合はSNBT直接編集

3. **エラー処理**:
   - 最大5回再試行
   - 行数不一致時はスキップ

## 貢献

- バグ報告・機能要望: GitHub Issuesへ
- フォーク大歓迎: `init.py`で主要パラメータ調整可能

## ライセンス

[MIT License](LICENSE)
