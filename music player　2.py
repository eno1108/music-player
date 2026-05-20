import tkinter as tk
from tkinter import filedialog
import tkinter.messagebox as messagebox
import pygame # type: ignore
import os
from mutagen.mp3 import MP3 # MP3ファイルの長さを取得するため

class MusicPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("音楽プレーヤー")
        self.root.geometry("500x570")
        
        # 明示的なパラメータでミキサーを初期化
        self.mixer_ok = False
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)
            self.mixer_ok = True
        except Exception as e:
            messagebox.showwarning("Audio Init Error", f"オーディオデバイスの初期化に失敗しました。音声再生は利用できません。\n{e}")

        self.track = tk.StringVar(value="--")
        self.status = tk.StringVar(value="Ready")

        tk.Label(root, text="曲名:").pack()
        tk.Label(root, textvariable=self.track).pack()
        tk.Label(root, textvariable=self.status, fg="blue").pack()
        
        # ファイル操作ボタン
        file_frame = tk.Frame(root)
        file_frame.pack(pady=5)
        tk.Button(file_frame, text="ファイルを開く", command=self.load).pack(side=tk.LEFT, padx=5)
        tk.Button(file_frame, text="選択した曲を削除", command=self.delete_selected).pack(side=tk.LEFT, padx=5)

        # --- 🎵 再生バー (シークバー) UIの初期化 ---
        self.current_time_var = tk.DoubleVar()
        self.time_frame = tk.Frame(root)
        self.time_frame.pack(pady=5)

        self.current_time_label = tk.Label(self.time_frame, text="00:00")
        self.current_time_label.pack(side=tk.LEFT, padx=5)
        
        self.seek_scale = tk.Scale(self.time_frame, from_=0, to=100, orient=tk.HORIZONTAL, variable=self.current_time_var, length=300)
        self.seek_scale.pack(side=tk.LEFT)
        
        self.duration_label = tk.Label(self.time_frame, text="00:00")
        self.duration_label.pack(side=tk.LEFT, padx=5)
        self.song_duration = 0
        
        # ★ シーク安定化のためのバインド設定とフラグ ★
        self.is_seeking = False # ユーザーがスライダーを操作中かどうかのフラグ
        self.seek_scale.bind("<ButtonPress-1>", self.start_seek) # 押されたとき
        self.seek_scale.bind("<ButtonRelease-1>", self.end_seek) # 離されたとき
        # -----------------------------------------------

        # 再生コントロールボタン
        control_frame = tk.Frame(root)
        control_frame.pack()
        tk.Button(control_frame, text="前へ", command=self.prev_song).pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="再生", command=self.play).pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="一時停止", command=self.pause).pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="停止", command=self.stop).pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="次へ", command=self.next_song).pack(side=tk.LEFT, padx=5)

        # 音量コントロール
        vol_frame = tk.Frame(root)
        vol_frame.pack(pady=6)
        tk.Label(vol_frame, text="Volume:").pack(side=tk.LEFT)
        self.volume_var = tk.IntVar(value=80)
        self.vol_scale = tk.Scale(vol_frame, from_=0, to=100, orient=tk.HORIZONTAL, variable=self.volume_var, command=self.on_volume_change, length=200)
        self.vol_scale.pack(side=tk.LEFT, padx=6)
        tk.Button(vol_frame, text="-", width=3, command=lambda: self.change_volume(-5)).pack(side=tk.LEFT)
        tk.Button(vol_frame, text="+", width=3, command=lambda: self.change_volume(+5)).pack(side=tk.LEFT)
        self.vol_label = tk.Label(vol_frame, text=f"{self.volume_var.get()}%")
        self.vol_label.pack(side=tk.LEFT, padx=6)

        # プレイリスト
        self.listbox = tk.Listbox(root, width=50, height=15)
        self.listbox.pack(pady=10)
        self.listbox.bind('<<ListboxSelect>>', self.on_select)

        self.paused = False
        self.playlist = []
        self.current = 0
        self.loaded = False
        
        # 初期音量の設定
        if self.mixer_ok:
            try:
                self.initial_volume = max(0.0, min(1.0, self.volume_var.get() / 100.0))
                pygame.mixer.music.set_volume(self.initial_volume)
            except Exception:
                 pass 

        # 再生終了チェックと再生バーの更新を1秒ごとに実行
        self.root.after(1000, self.check_music_end)

    # --- ヘルパーメソッド ---
    def format_time(self, seconds):
        """秒数を 'mm:ss' 形式の文字列に変換"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"

    # --- シーク操作メソッド ---
    def start_seek(self, event):
        """スライダーを押したときに呼び出され、自動更新を停止する"""
        self.is_seeking = True

    def end_seek(self, event):
        """スライダーを放したときに呼び出され、シークを実行する"""
        if not self.playlist or not self.loaded or not self.mixer_ok:
            self.is_seeking = False
            return
            
        target_time_seconds = self.current_time_var.get()

        try:
            # マウスを放した位置から再生を再開
            pygame.mixer.music.play(start=target_time_seconds)
            self.status.set(f"Seeking to {self.format_time(int(target_time_seconds))}")
            self.paused = False 
        except Exception as e:
            print(f"Seek Error: {e}")
            self.status.set("Seek Error")
            
        self.is_seeking = False # シーク完了後にフラグをリセット

    # --- プレイリスト・ファイル操作メソッド ---
    def load(self):
        files = filedialog.askopenfilenames(filetypes=[("MP3 files", "*.mp3")])
        if files:
            self.playlist = list(files)
            self.listbox.delete(0, tk.END)
            for f in self.playlist:
                self.listbox.insert(tk.END, os.path.basename(f))
            self.current = 0
            self.select_song(0)

    def select_song(self, idx):
        if not self.playlist:
            self.track.set("--")
            self.status.set("Ready")
            self.loaded = False
            self.seek_scale.config(to=0)
            self.seek_scale.set(0)
            self.current_time_label.config(text="00:00")
            self.duration_label.config(text="00:00")
            return
            
        self.current = idx
        current_file = self.playlist[self.current]
        self.track.set(os.path.basename(current_file))
        self.loaded = False
        
        if not self.mixer_ok:
            self.status.set("Audio Init Error")
            return
            
        try:
            pygame.mixer.music.load(current_file)
            self.status.set("Loaded")
            self.loaded = True
            
            # Mutagenで曲の総再生時間を取得
            audio = MP3(current_file)
            self.song_duration = int(audio.info.length)
            
            # 再生バーの最大値を設定し、最初に戻す
            self.seek_scale.config(to=self.song_duration)
            self.seek_scale.set(0)
            
            self.duration_label.config(text=self.format_time(self.song_duration))
            self.current_time_label.config(text="00:00")
            
            current_vol = self.volume_var.get() / 100.0
            pygame.mixer.music.set_volume(current_vol)

        except Exception as e:
            self.loaded = False
            msg = f"曲を読み込めません: {os.path.basename(current_file)}\n\n詳細: {e}"
            msg += "\n\n対処法: ffmpeg で再エンコードしてみてください。例:\nffmpeg -i \"input.mp3\" -codec:a libmp3lame -qscale:a 2 \"fixed.mp3\""
            messagebox.showerror("読み込みエラー", msg)
            self.status.set("Load Error")
            
        self.listbox.select_clear(0, tk.END)
        self.listbox.select_set(self.current)
        self.listbox.activate(self.current)

    def delete_selected(self):
        if not self.listbox.curselection():
            return
        
        selected_indices = self.listbox.curselection()
        idx_to_remove = max(selected_indices) 
        
        if idx_to_remove == self.current and self.mixer_ok and pygame.mixer.music.get_busy():
            self.stop()
            
        self.listbox.delete(idx_to_remove)
        del self.playlist[idx_to_remove]
        
        if not self.playlist:
            self.track.set("--")
            self.status.set("Ready")
            self.loaded = False
            self.current = 0
            self.seek_scale.config(to=0)
            self.seek_scale.set(0)
            self.current_time_label.config(text="00:00")
            self.duration_label.config(text="00:00")
            
        elif idx_to_remove == self.current:
            if self.current >= len(self.playlist):
                self.current = 0 
            self.select_song(self.current) 
            self.status.set("Loaded (Deleted Current)")
            
        elif idx_to_remove < self.current:
            self.current -= 1
            self.listbox.select_set(self.current)
            self.listbox.activate(self.current)
        else:
            self.listbox.select_set(self.current)
            self.listbox.activate(self.current)

    # --- 再生コントロールメソッド ---
    def play(self):
        if not self.playlist or not self.loaded:
            self.status.set("ファイルを選択してください" if not self.playlist else "曲が読み込まれていません")
            return
        if not self.mixer_ok:
            self.status.set("オーディオ未初期化")
            return
            
        if self.paused:
            pygame.mixer.music.unpause()
            self.paused = False
        else:
            pygame.mixer.music.play()
            
        self.status.set("Playing")
        
    def pause(self):
        if self.playlist and self.mixer_ok:
            pygame.mixer.music.pause()
            self.paused = True
            self.status.set("Paused")

    def stop(self):
        if self.playlist and self.mixer_ok:
            pygame.mixer.music.stop()
            self.seek_scale.set(0)
            self.current_time_label.config(text="00:00")
            self.paused = False 
            self.status.set("Stopped")

    def next_song(self):
        if self.playlist:
            new_index = (self.current + 1) % len(self.playlist) 
            self.select_song(new_index)
            self.play()

    def prev_song(self):
        if self.playlist:
            new_index = (self.current - 1 + len(self.playlist)) % len(self.playlist) 
            self.select_song(new_index)
            self.play()

    def on_select(self, event):
        if self.listbox.curselection():
            idx = self.listbox.curselection()[0]
            if idx != self.current: 
                self.select_song(idx)
                self.play()

    # --- 音量コントロールメソッド ---
    def on_volume_change(self, val):
        try:
            pct = int(float(val))
        except Exception:
            return
        self.vol_label.config(text=f"{pct}%")
        if self.mixer_ok:
            try:
                pygame.mixer.music.set_volume(pct / 100.0)
            except Exception:
                pass

    def change_volume(self, delta):
        cur = self.volume_var.get()
        new = max(0, min(100, cur + delta))
        self.volume_var.set(new)
        self.on_volume_change(new)
        
    # --- 再生バー更新と自動再生機能 ---
    def check_music_end(self):
        
        # 🎵 再生バーと現在時刻の更新（再生中の場合のみ）
        if self.playlist and self.loaded and self.mixer_ok and pygame.mixer.music.get_busy():
            pos_ms = pygame.mixer.music.get_pos()
            current_sec = int(pos_ms / 1000)
            
            # ユーザーがスライダーを操作していない時のみ、再生位置を自動更新する
            if not self.is_seeking:
                self.seek_scale.set(current_sec)
                
            self.current_time_label.config(text=self.format_time(current_sec))

            # 再生位置が総再生時間に達した場合の強制スキップロジック
            if self.song_duration > 0 and current_sec >= self.song_duration:
                self.paused = False 
                pygame.mixer.music.stop()
                self.status.set("Song Ended (Auto-Skip Triggered)")
                
        # 🔊 自動再生処理（再生が完全に終了し、かつ一時停止中でない場合）
        if self.playlist and self.loaded and self.mixer_ok and not pygame.mixer.music.get_busy() and not self.paused:
             self.status.set("Song Ended")
             
             # 次の曲へ自動再生
             new_index = (self.current + 1) % len(self.playlist) 
             self.select_song(new_index)
             self.play()
             
        # ポーリングを継続
        self.root.after(1000, self.check_music_end)


if __name__ == "__main__":
    root = tk.Tk()
    app = MusicPlayer(root)
    root.mainloop()