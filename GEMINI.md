# 熊本カフェ紹介ウェブサイトジェネレーター

## プロジェクト概要
このプロジェクトは、TikTok動画からカフェの情報を抽出し、それらを整理してウェブサイトとして公開するためのツールです。動画のダウンロード、音声の文字起こし、画像からのテキスト認識（OCR）、動画からのキーフレーム抽出、そしてそれらの情報を基にしたHTMLウェブサイトの自動生成を行います。

## 主要ファイルと役割
- `cafes.json`: 各カフェの詳細情報（名前、TikTok URL、住所、説明、メニュー概要、関連リンクなど）をJSON形式で管理します。新しいカフェを追加する際や既存の情報を更新する際に編集します。
- `template.html`: 各カフェの個別ページ（例: `cafe1/index.html`）のHTML構造を定義するJinja2テンプレートです。サイドバーやギャラリー、動画プレイヤーなどの共通レイアウトが含まれます。
- `main_index_template.html`: ウェブサイトのトップページ（`index.html`）のHTML構造を定義するJinja2テンプレートです。各カフェへのリンクカードが含まれます。
- `_cafe_navigation_template.html`: 各カフェの個別ページに表示されるサイドバーのナビゲーション部分のHTML構造を定義するJinja2テンプレートです。`generate_html.py`によって`_cafe_navigation.html`として生成され、`template.html`からインクルードされます。
- `style.css`: ウェブサイト全体のスタイル（CSS）を定義します。レイアウト、色、フォント、レスポンシブデザインなどが含まれます。
- `process_videos.py`: TikTok動画のダウンロード、音声抽出、文字起こし、OCR、キーフレーム抽出といった、時間のかかる動画処理全般を担当します。新しいカフェの追加や既存動画の再処理に使用します。
- `generate_html.py`: `cafes.json`と各種HTMLテンプレートを読み込み、各カフェの個別HTMLファイル（例: `cafe1/index.html`）とウェブサイトのトップページ（`index.html`）を生成します。
- `venv_tiktok/`: プロジェクトのPython仮想環境です。必要なライブラリがインストールされています。
- `old/`: 以前のバージョンで生成された不要なファイルや、手動で移動された古いファイルを格納するディレクトリです。

## 主要ワークフロー

### 1. 新しいカフェを追加する / 新しいTikTok動画を処理する
新しいTikTok動画のURLを基にカフェを追加したり、既存の動画データを再処理したりする場合に使用します。

**コマンド:**
```bash
D:\AI\geminiCLI\venv_tiktok\Scripts\python.exe D:\AI\geminiCLI\process_videos.py --url <TikTokのURL>
```
**例:**
```bash
D:\AI\geminiCLI\venv_tiktok\Scripts\python.exe D:\AI\geminiCLI\process_videos.py --url https://vt.tiktok.com/ZSBedhYM6/
```

**説明:**
- このコマンドを実行すると、指定されたURLの動画がダウンロードされ、音声抽出、文字起こし、OCR、キーフレーム抽出が行われます。
- `cafes.json`に新しいカフェのエントリが追加されます（初期情報はプレースホルダーです）。
- **重要:** 動画処理が完了した後、`generate_html.py`が自動的に呼び出され、ウェブサイト全体が更新されます。
- **Googleマップからの情報取得と`cafes.json`の自動更新**: `process_videos.py`が動画処理を完了すると、OCRや文字起こしから得られた情報を元に、私（Geminiエージェント）が内部ツール（Google検索やウェブコンテンツ取得など）を活用してGoogleマップを検索し、カフェの情報を自動で抽出・更新します。その後、`cafes.json`が更新され、ウェブサイトに反映されます。
- `--url`引数を省略して実行した場合（`D:\AI\geminiCLI\venv_tiktok\Scripts\python.exe D:\AI\geminiCLI\process_videos.py`）、`cafes.json`に登録されている全てのカフェの動画が再処理されます。

### 2. 既存のカフェ情報を手動で更新する (`cafes.json` を編集した場合)
`cafes.json` を直接編集して、カフェの名前、住所、説明などの情報を更新した場合に使用します。

**コマンド:**
```bash
D:\AI\geminiCLI\venv_tiktok\Scripts\python.exe D:\AI\geminiCLI\generate_html.py
```
**説明:**
- このコマンドは、`cafes.json`の最新情報と各種HTMLテンプレートを基に、ウェブサイト全体を再生成します。動画処理は行われません。

### 3. HTMLテンプレート (`template.html`, `main_index_template.html`, `_cafe_navigation_template.html`) やスタイルシート (`style.css`) を更新する
ウェブサイトの見た目やレイアウトを変更した場合に使用します。

**コマンド:**
```bash
D:\AI\geminiCLI\venv_tiktok\Scripts\python.exe D:\AI\geminiCLI\generate_html.py
```
**説明:**
- このコマンドは、更新されたテンプレートやスタイルシートを基に、ウェブサイト全体を再生成します。

## エージェント連携プロトコル
このセクションは、Geminiエージェントが`process_videos.py`スクリプトと連携し、`cafes.json`の自動更新プロセスを自動化する方法を記述します。

`process_videos.py`が`--url`引数付きで実行されると、標準出力に以下の形式のメッセージを出力します。

`AGENT_REQUEST_GOOGLE_MAPS_INFO: {"cafe_id": "cafeX", "search_query": "..."}`

このメッセージを検知した場合、エージェントは以下の手順を実行する必要があります。

1.  **メッセージの解析**: JSONペイロードから`cafe_id`と`search_query`を抽出します。
2.  **Googleマップの検索**: 
    *   `process_videos.py`から受け取った`search_query`を参考に、カフェ名や住所などのエンティティを抽出し、より的確なGoogleマップ検索クエリを生成します。
    *   `default_api.google_web_search(query=f"{生成した検索クエリ} Google Maps")`を実行します。
    *   検索結果の`results`を分析し、関連するGoogleマップのURL（例: "maps.google.com"または"goo.gl/maps"を含むもの）を見つけます。公式のGoogleマップリンクを優先します。
3.  **Googleマップコンテンツの取得**: 
    *   GoogleマップのURLが見つかった場合、`default_api.web_fetch(prompt=f"Get content from {maps_url}")`を実行します。
    *   **重要**: Googleマップから取得されるコンテンツは生のHTMLです。Googleマップのウェブ構造は頻繁に変更されるため、構造化されたデータをこのHTMLから抽出することは複雑で壊れやすいです。エージェントは、その内部能力（例: パターンマッチング、コンテキスト理解）を使用して、以下の情報を可能な限り抽出する必要があります。
        *   カフェ名
        *   住所
        *   電話番号（利用可能な場合）
        *   営業時間（利用可能な場合）
        *   説明/概要（利用可能な場合）
        *   その他の関連する`info`フィールド
4.  **`cafes.json`の更新**: 
    *   `default_api.read_file(absolute_path="D:\AI\geminiCLI\cafes.json")`を使用して現在の`cafes.json`を読み込みます。
    *   一致する`cafe_id`のエントリを見つけます。
    *   抽出した情報で、このエントリの`name`、`address`、`description`、および`info`フィールドを更新します。
    *   `default_api.write_file(content=json.dumps(updated_data, ensure_ascii=False, indent=2), file_path="D:\AI\geminiCLI\cafes.json")`を使用して、更新された`cafes.json`を書き戻します。
5.  **HTMLの再生成**: 
    *   `cafes.json`の更新後、`default_api.run_shell_command(command="D:\AI\geminiCLI\venv_tiktok\Scripts\python.exe D:\AI\geminiCLI\generate_html.py", description="Regenerate HTML after cafes.json update.")`を実行します。

## 環境と依存関係
- **Python仮想環境**: `venv_tiktok/` にセットアップされています。
- **外部ツール**: `ffmpeg` がシステムPATHに設定されている必要があります。
- **Pythonライブラリ**: `yt-dlp`, `whisper`, `opencv-python`, `easyocr`, `requests`, `Jinja2` が `venv_tiktok` 内にインストールされています。

## ドキュメント管理
- この`GEMINI.md`ファイルは、プロジェクトのワークフロー、使用ツール、およびエージェントの内部プロセスにおける重要な変更を反映するために、適宜更新されます。

## 特記事項と制限事項
- **Googleマップの埋め込み**: 基本的なGoogleマップの埋め込み（iframeを使用する形式）にはAPIキーは不要です。より高度な機能（JavaScript APIなど）を利用する場合にのみAPIキーが必要となります。
- **ファイル整理**: `old/` ディレクトリは、手動で不要なファイルを移動するためのものです。特殊文字を含むファイル名の場合、`move`コマンドで移動できないことがあります。その際は、ファイルエクスプローラーで手動で移動してください。
- **ブラウザのキャッシュ**: HTMLやCSSの変更がブラウザに反映されない場合は、ブラウザのキャッシュをクリアするために**ハードリロード**（Ctrl + Shift + R または Cmd + Shift + R）を試してください。