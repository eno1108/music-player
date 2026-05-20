import pygame
import os
import time

# --- Pygame Mixer の初期化 ---
try:pygame.mixer.init()
except pygame.error as e:
    print(f"Pygameミキサーの初期化中にエラーが発生しました: {e}")
    print("オーディオドライバが正しくインストールされ、動作していることを確認してください。")
    exit() # ミキサーが初期化できない場合は終了

# --- 音楽フォルダのパス ---
music_folder = "F:\\pc\\music"  # バックスラッシュを二重にする
# 音楽フォルダが存在するかどうかを検証
if not os.path.isdir(music_folder):
    print(f"エラー: 指定された音楽フォルダが見つかりません: {music_folder}")
    exit()

# --- MP3ファイルの取得 ---
# フォルダ内のMP3ファイルを取得し、名前順にソート
music_files = sorted([f for f in os.listdir(music_folder) if f.endswith('.mp3')])

if not music_files:
    print(f"指定されたフォルダにMP3ファイルが見つかりませんでした: {music_folder}")
else:
    # --- 音楽リストの表示 ---
    print("\n--- 利用可能な曲 ---")
    for idx, file in enumerate(music_files):
        print(f"{idx + 1}: {file}")
    print("-----------------------\n")

    current_song_index = -1 # 現在再生中の曲のインデックスを追跡

    try:
        while True:
            # --- 曲の選択またはコマンドの入力 ---
            choice_input = input("再生する曲の番号を入力してください。または 'p'(一時停止), 'r'(再開), 's'(停止), 'exit'(終了) を入力: ").strip().lower()

            if choice_input == 'exit':
                break
            elif choice_input == 'p': # 一時停止コマンド
                if pygame.mixer.music.get_busy(): # 現在再生中かチェック
                    pygame.mixer.music.pause()
                    print("音楽を一時停止しました。")
                else:
                    print("再生中の音楽がありません。")
            elif choice_input == 'r': # 再開コマンド
                # get_pos() が -1 でない（一度ロードされている）かつ再生中でない（一時停止中）かチェック
                if pygame.mixer.music.get_pos() != -1 and not pygame.mixer.music.get_busy(): 
                    pygame.mixer.music.unpause()
                    print("音楽を再開しました。")
                else:
                    print("一時停止中の音楽がありません。")
            elif choice_input == 's': # 停止コマンド
                if pygame.mixer.music.get_busy():
                    pygame.mixer.music.stop()
                    print("音楽を停止しました。")
                    current_song_index = -1 # 現在の曲情報をリセット
                else:
                    print("再生中の音楽がありません。")
            else:
                # --- 新しい曲の再生を試みる ---
                try:
                    choice_num = int(choice_input) - 1 # ユーザー入力（1から始まる）を0始まりのインデックスに変換
                    if 0 <= choice_num < len(music_files): # 有効な番号かチェック
                        file_path = os.path.join(music_folder, music_files[choice_num])
                        pygame.mixer.music.load(file_path) # 曲をロード
                        pygame.mixer.music.play(-1)  # 無限ループで再生
                        current_song_index = choice_num
                        print(f"再生中: {music_files[current_song_index]}")
                    else:
                        print("無効な曲の番号です。リストから番号を選択してください。")
                except ValueError:
                    print("無効な入力です。曲の番号、または 'p', 'r', 's', 'exit' のいずれかを入力してください。")

    except KeyboardInterrupt:
        # Ctrl+Cでの終了を gracefully に処理
        print("\nプレイヤーを終了します。")
    finally:
        # プログラム終了時に音楽を停止し、ミキサーのリソースを解放
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
        pygame.mixer.quit() # Pygameミキサーを終了
        print("音楽プレイヤーが閉じられました。")
