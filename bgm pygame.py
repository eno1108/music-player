import pygame
import os
import time
import msvcrt  # Windows専用

# --- Pygame Mixer の初期化 ---
try:
    pygame.mixer.init()
except pygame.error as e:
    print(f"Pygameミキサーの初期化中にエラーが発生しました: {e}")
    exit()

music_folder = "F:\\pc\\music"

if not os.path.isdir(music_folder):
    print(f"エラー: 指定された音楽フォルダが見つかりません: {music_folder}")
    exit()

music_files = sorted([f for f in os.listdir(music_folder) if f.endswith('.mp3')])

if not music_files:
    print(f"指定されたフォルダにMP3ファイルが見つかりませんでした: {music_folder}")
    exit()

print("\n--- 利用可能な曲 ---")
for idx, file in enumerate(music_files):
    print(f"{idx + 1}: {file}")
print("-----------------------\n")

current_song_index = -1
play_queue = list(range(len(music_files)))

def play_next_in_queue():
    global current_song_index
    while play_queue:
        current_song_index = play_queue.pop(0)
        file_path = os.path.join(music_folder, music_files[current_song_index])
        try:
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            print(f"再生中: {music_files[current_song_index]}")
            return
        except Exception as e:
            print(f"ファイル再生エラー: {music_files[current_song_index]} ({e})")
            continue
    print("再生キューが空です。")

try:
    if play_queue:
        play_next_in_queue()

    buffer = ""
    print("コマンド: 'p'(一時停止), 'r'(再開), 's'(停止), 'n'(次へ), 'seek 秒'(シーク), 'pos'(現在位置), 'exit'(終了), [曲番号]")

    last_update = time.time()
    update_interval = 60  # 1分（60秒）

    while True:
        if not pygame.mixer.music.get_busy() and play_queue:
            play_next_in_queue()

        # 1分ごとに現在の曲と再生位置を表示
        now = time.time()
        if now - last_update > update_interval:
            if current_song_index != -1:
                pos_ms = pygame.mixer.music.get_pos()
                print(f"\n--- 現在の曲 ---")
                print(f"{music_files[current_song_index]}")
                if pos_ms != -1:
                    print(f"再生位置: {pos_ms/1000:.1f} 秒")
                print("-----------------------\n")
            last_update = now

        # ノンブロッキングでキー入力を取得
        if msvcrt.kbhit():
            char = msvcrt.getwch()
            if char == '\r':  # Enter
                choice_input = buffer.strip().lower()
                buffer = ""
                if choice_input == 'exit':
                    break
                elif choice_input == 'p':
                    if pygame.mixer.music.get_busy():
                        pygame.mixer.music.pause()
                        print("音楽を一時停止しました。")
                    else:
                        print("再生中の音楽がありません。")
                elif choice_input == 'r':
                    if pygame.mixer.music.get_pos() != -1 and not pygame.mixer.music.get_busy():
                        pygame.mixer.music.unpause()
                        print("音楽を再開しました。")
                    else:
                        print("一時停止中の音楽がありません。")
                elif choice_input == 's':
                    if pygame.mixer.music.get_busy():
                        pygame.mixer.music.stop()
                        print("音楽を停止しました。")
                        current_song_index = -1
                    else:
                        print("再生中の音楽がありません。")
                elif choice_input == 'n':
                    play_next_in_queue()
                elif choice_input.startswith('seek '):
                    try:
                        sec = float(choice_input.split()[1])
                        if current_song_index != -1:
                            file_path = os.path.join(music_folder, music_files[current_song_index])
                            pygame.mixer.music.load(file_path)
                            pygame.mixer.music.play(start=sec)
                            print(f"{sec}秒から再生しました。")
                        else:
                            print("再生中の曲がありません。")
                    except Exception as e:
                        print(f"シークに失敗しました: {e}")
                elif choice_input == 'pos':
                    pos_ms = pygame.mixer.music.get_pos()
                    if pos_ms != -1:
                        print(f"現在の再生位置: {pos_ms/1000:.1f} 秒")
                    else:
                        print("再生中の曲がありません。")
                elif choice_input.strip().isdigit():
                    num = int(choice_input.strip())
                    if 1 <= num <= len(music_files):
                        pygame.mixer.music.stop()
                        current_song_index = num - 1
                        file_path = os.path.join(music_folder, music_files[current_song_index])
                        pygame.mixer.music.load(file_path)
                        pygame.mixer.music.play()
                        print(f"ジャンプ: {music_files[current_song_index]}")
                        play_queue = list(range(current_song_index + 1, len(music_files)))
                    else:
                        print("曲番号が範囲外です。")
                else:
                    print("無効な入力です。'p', 'r', 's', 'n', 'seek 秒', 'pos', 'exit' または曲番号を入力してください。")
            elif char == '\b':  # バックスペース
                buffer = buffer[:-1]
            else:
                buffer += char

        time.sleep(0.1)  # CPU負荷軽減

except KeyboardInterrupt:
    print("\nプレイヤーを終了します。")
finally:
    if pygame.mixer.music.get_busy():
        pygame.mixer.music.stop()
    pygame.mixer.quit()
    print("音楽プレイヤーが閉じられました。")
