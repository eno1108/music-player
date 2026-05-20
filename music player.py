import tkinter as tk
from tkinter import filedialog
import tkinter.messagebox as messagebox
import pygame # type: ignore
import os

class MusicPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("音楽プレーヤー")
        self.root.geometry("500x500")
        
        # 明示的なパラメータでミキサーを初期化（互換性向上）
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
                 # ミキサー初期化OKでもボリューム設定に失敗することがある
                pass 

        # 再生終了チェックを1秒ごとに実行
        self.root.after(1000, self.check_music_end)

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
            return
            
        self.current = idx
        current_file = self.playlist[self.current]
        self.track.set(os.path.basename(current_file))
        self.loaded = False # 読み込み開始時は False にリセット
        
        if not self.mixer_ok:
            self.status.set("Audio Init Error")
            return
            
        try:
            # Pygameでファイルをロード
            pygame.mixer.music.load(current_file)
            self.status.set("Loaded")
            self.loaded = True
            
            # 読み込み後に現在のボリュームを適用
            current_vol = self.volume_var.get() / 100.0
            pygame.mixer.music.set_volume(current_vol)

        except Exception as e:
            # 読み込みエラー（壊れた mp3 等）をユーザに通知してスキップ
            msg = f"曲を読み込めません: {os.path.basename(current_file)}\n\n詳細: {e}"
            msg += "\n\n対処法: ffmpeg で再エンコードしてみてください。例:\nffmpeg -i \"input.mp3\" -codec:a libmp3lame -qscale:a 2 \"fixed.mp3\""
            messagebox.showerror("読み込みエラー", msg)
            self.status.set("Load Error")
            
        # UIの選択状態を更新
        self.listbox.select_clear(0, tk.END)
        self.listbox.select_set(self.current)
        self.listbox.activate(self.current)

    def play(self):
        if not self.playlist or not self.loaded:
            if not self.playlist:
                self.status.set("ファイルを選択してください")
            else:
                 self.status.set("曲が読み込まれていません")
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

    def pause(self):
        if self.playlist and self.mixer_ok:
            pygame.mixer.music.pause()
            self.paused = True
            self.status.set("Paused")

    def stop(self):
        if self.playlist and self.mixer_ok:
            pygame.mixer.music.stop()
            self.paused = False # 停止後は一時停止状態をリセット
            self.status.set("Stopped")

    def next_song(self):
        if self.playlist:
            new_index = (self.current + 1) % len(self.playlist) # 次の曲へ、最後なら最初へ
            self.select_song(new_index)
            self.play()

    def prev_song(self):
        if self.playlist:
            new_index = (self.current - 1 + len(self.playlist)) % len(self.playlist) # 前の曲へ、最初なら最後へ
            self.select_song(new_index)
            self.play()

    def on_select(self, event):
        if self.listbox.curselection():
            idx = self.listbox.curselection()[0]
            if idx != self.current: # 違う曲が選択された場合のみ
                self.select_song(idx)
                self.play()

    def check_music_end(self):
        # プレイリストがあり、再生中でなく、一時停止中でない（つまり再生が終了した）場合
        if self.playlist and self.loaded and self.mixer_ok and not pygame.mixer.music.get_busy() and not self.paused:
            self.status.set("Song Ended")
            # 次の曲へ自動再生
            new_index = (self.current + 1) % len(self.playlist) # 次の曲へ、最後なら最初へ
            self.select_song(new_index)
            self.play()
            
        self.root.after(1000, self.check_music_end) # 1秒後に再度チェック
        
    def delete_selected(self):
        if not self.listbox.curselection():
            return
        
        selected_indices = self.listbox.curselection()
        # 複数のアイテムが選択されていても、単一の削除操作として処理するため、
        # 選択されたインデックスの中で最大のものを取得
        idx_to_remove = max(selected_indices) 
        
        # 削除する曲が現在再生中の曲の場合、停止する
        if idx_to_remove == self.current and self.mixer_ok and pygame.mixer.music.get_busy():
            self.stop()
            
        # リストボックスとプレイリストから削除
        self.listbox.delete(idx_to_remove)
        del self.playlist[idx_to_remove]
        
        # current の調整
        if not self.playlist:
            self.track.set("--")
            self.status.set("Ready")
            self.loaded = False
            self.current = 0
            
        elif idx_to_remove == self.current:
            # 再生中の曲が削除され、次の曲へ進む必要がある場合
            if self.current >= len(self.playlist):
                self.current = 0 # 最後の曲が削除された場合、先頭へ
            # 削除後、新しい current の曲を読み込む（再生はしない）
            self.select_song(self.current) 
            self.status.set("Loaded (Deleted Current)")
            
        elif idx_to_remove < self.current:
            # 削除された曲が現在の曲よりも前の場合、current をデクリメント
            self.current -= 1
            self.listbox.select_set(self.current)
            self.listbox.activate(self.current)
        else:
             # 削除された曲が現在の曲よりも後の場合、current は変わらない
            self.listbox.select_set(self.current)
            self.listbox.activate(self.current)


if __name__ == "__main__":
    root = tk.Tk()
    app = MusicPlayer(root)
    root.mainloop()