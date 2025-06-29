# 熊本カフェ紹介ウェブサイトジェネレーター

## プロジェクト概要
このプロジェクトは、TikTok動画からカフェの情報を抽出し、それらを整理してウェブサイトとして公開するためのツールです。動画のダウンロード、音声の文字起こし、画像からのテキスト認識（OCR）、動画からのキーフレーム抽出、そしてそれらの情報を基にしたHTMLウェブサイトの自動生成を行います。

## 主要ファイルと役割
- `cafes.json`: 各カフェの詳細情報（名前、TikTok URL、住所、説明、メニュー概要、関連リンクなど）をJSON形式で管理します。
- `template.html`: 各カフェの個別ページ（例: `cafe1/index.html`）のHTML構造を定義するJinja2テンプレートです。
- `main_index_template.html`: ウェブサイトのトップページ（`index.html`）のHTML構造を定義するJinja2テンプレートです。
- `_cafe_navigation_template.html`: サイドバーのナビゲーション部分のHTML構造を定義するJinja2テンプレートです。
- `style.css`: ウェブサイト全体のスタイル（CSS）を定義します。
- `process_videos.py`: TikTok動画の処理（ダウンロード、音声抽出、文字起こし、OCR、キーフレーム抽出、メタデータ保存）を担当します。
- `generate_html.py`: `cafes.json`と各種HTMLテンプレートを読み込み、ウェブサイトを生成します。
- `venv_tiktok/`: プロジェクトのPython仮想環境です。
- `old/`: 以前のバージョンで生成された不要なファイルを格納するディレクトリです。

## 主要ワークフロー

### 1. 新しいカフェを追加する / 既存の動画を再処理する

**ユーザーが実行するコマンド:**
```bash
D:\AI\geminiCLI\venv_tiktok\Scripts\python.exe D:\AI\geminiCLI\process_videos.py --url <TikTokのURL>
```
**例:**
```bash
D:\AI\geminiCLI\venv_tiktok\Scripts\python.exe D:\AI\geminiCLI\process_videos.py --url https://vt.tiktok.com/ZSBedhYM6/
```

**エージェントの動作:**
- 指定されたURLの動画を処理（ダウンロード、音声抽出、文字起こし、OCR、キーフレーム抽出、TikTokメタデータ保存）します。
- `cafes.json`に新しいカフェのエントリが追加されます（初期情報はプレースホルダーです）。
- 動画処理完了後、`AGENT_REQUEST_GOOGLE_MAPS_INFO`メッセージを検知し、以下の自動処理を開始します。
    1.  **Googleマップ情報の取得**: OCRテキスト、文字起こしテキスト、**およびダウンロードされたTikTokの概要欄**を参考に、カフェ名や住所などのエンティティを抽出し、より的確なGoogleマップ検索クエリを生成します。その後、Google検索とウェブコンテンツ取得ツールを活用し、カフェの情報を可能な限り自動で抽出します。
    2.  **`cafes.json`の更新**: 抽出した情報で`cafes.json`の該当エントリを更新します。
    3.  **HTMLの再生成**: `generate_html.py`を自動的に呼び出し、ウェブサイト全体を更新します。

**補足:**
- `--url`引数を省略して実行した場合（`D:\AI\geminiCLI\venv_tiktok\Scripts\python.exe D:\AI\geminiCLI\process_videos.py`）、`cafes.json`に登録されている全てのカフェの動画が再処理され、上記のエージェントの自動処理も実行されます。

### 2. `cafes.json` またはHTMLテンプレート/スタイルシートを手動で更新する

**ユーザーが実行するコマンド:**
```bash
D:\AI\geminiCLI\venv_tiktok\Scripts\python.exe D:\AI\geminiCLI\generate_html.py
```
**エージェントの動作:**
- `cafes.json`の最新情報と各種HTMLテンプレートを基に、ウェブサイト全体を再生成します。動画処理は行われません。

## 環境と依存関係
- **Python仮想環境**: `venv_tiktok/` にセットアップされています。
- **外部ツール**: `ffmpeg` がシステムPATHに設定されている必要があります。
- **Pythonライブラリ**: `yt-dlp`, `whisper`, `opencv-python`, `easyocr`, `requests`, `Jinja2` が `venv_tiktok` 内にインストールされています。

## ドキュメント管理
- この`GEMINI.md`ファイルは、プロジェクトのワークフロー、使用ツール、およびエージェントの内部プロセスにおける重要な変更を反映するために、適宜更新されます。

## 特記事項と制限事項
- **Googleマップからの情報自動抽出の精度**: 私（Geminiエージェント）がGoogleマップから情報を自動抽出する機能は、ウェブサイトの構造が複雑で頻繁に変更されるため、完璧な精度を保証するものではありません。抽出された情報が不正確な場合は、手動で`cafes.json`を修正してください。
- **Googleマップの埋め込み**: 基本的なGoogleマップの埋め込み（iframeを使用する形式）にはAPIキーは不要です。より高度な機能（JavaScript APIなど）を利用する場合にのみAPIキーが必要となります。
- **ファイル整理**: `old/` ディレクトリは、手動で不要なファイルを移動するためのものです。特殊文字を含むファイル名の場合、`move`コマンドで移動できないことがあります。その際は、ファイルエクスプローラーで手動で移動してください。
- **ブラウザのキャッシュ**: HTMLやCSSの変更がブラウザに反映されない場合は、ブラウザのキャッシュをクリアするために**ハードリロード**（Ctrl + Shift + R または Cmd + Shift + R）を試してください。
