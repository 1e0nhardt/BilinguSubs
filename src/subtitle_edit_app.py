from dataclasses import dataclass
from functools import partial
import os

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.icons import Emoji
from tkinter import filedialog

from src.srt_container import SrtClip, SrtContainer
from src.video_player import MediaPlayer
from src.subtitle_editor import SubtitleEditor
from src.config import AppConfig
from src.whisper_agent import WhisperAgent
from utils import LOGGER, timeline_to_ms

@dataclass
class AppState:

    playing: bool = False


class Application(ttk.Window):

    def __init__(self, title, theme_name='yeti', **args) -> None:
        super().__init__(title, theme_name, **args)
        self.state = AppState()
        self.config = AppConfig()
        self.srt_container = SrtContainer()
        # self.srt_container.load_srt(self.config.srt_dir + "Creating a Cozy Pixel Campfire for a Roguelike Deckbuilder (S02E07).srt")
        self.agent = WhisperAgent(self.config)
        self.task_progress_value = ttk.DoubleVar()

        self.hdr_var = ttk.StringVar()
        # self.create_header()
        self.mp = MediaPlayer(self)
        self.create_buttonbox()
        self.editor = SubtitleEditor(self)
        self.next_editor = SubtitleEditor(self, next=True)
        self.play(self.config.video_path)

        self.editor.load_clip(self.srt_container.get_current_clip())
        self.next_editor.load_clip(self.srt_container.get_current_next_clip())

    def create_header(self):
        """The application header to display user messages"""
        self.hdr_var.set("Open a file to begin playback")
        lbl = ttk.Label(
            master=self,
            textvariable=self.hdr_var,
            bootstyle=(LIGHT, INVERSE),
            padding=10
        )
        lbl.pack(fill=X, expand=YES)

    def create_buttonbox(self):
        """Create buttonbox with media controls"""
        container = ttk.Frame(self)
        container.pack(fill=X, expand=YES)
        ttk.Style().configure('TButton', font="-size 14")

        self.play_btn = ttk.Button(
            master=container,
            text=Emoji.get('black right-pointing triangle'),
            padding=10,
            command=self.on_play_button_click
        )
        self.play_btn.pack(side=LEFT, fill=X, expand=YES)
        self.bind('<space>', self.on_play_button_click)

        stop_btn = ttk.Button(
            master=container,
            text=Emoji.get('black square for stop'),
            padding=10,
            command=lambda: self.stop()
        )
        stop_btn.pack(side=LEFT, fill=X, expand=YES)

        file_btn = ttk.Button(
            master=container,
            text="加载字幕文件",
            # bootstyle=SECONDARY,
            padding=10,
            command=partial(self.on_open_file, 'srt')
        )
        file_btn.pack(side=LEFT, fill=X, expand=YES)

        file_btn = ttk.Button(
            master=container,
            text="打开视频文件",
            # bootstyle=SECONDARY,
            padding=10,
            command=partial(self.on_open_file, 'video')
        )
        file_btn.pack(side=LEFT, fill=X, expand=YES)
        
        prev_btn = ttk.Button(
            master=container,
            text="跳转到前一个片段",
            # bootstyle=SECONDARY,
            padding=10,
            command=lambda: self.on_clip_nav(next=False)
        )
        prev_btn.pack(side=LEFT, fill=X, expand=YES)
        
        next_btn = ttk.Button(
            master=container,
            text="跳转到后一个片段",
            # bootstyle=SECONDARY,
            padding=10,
            command=lambda: self.on_clip_nav(next=True)
        )
        next_btn.pack(side=LEFT, fill=X, expand=YES)

        clip_start_btn = ttk.Button(
            master=container,
            text="当前片段生成",
            # bootstyle=SECONDARY,
            padding=10,
            command=lambda: self.update_clip(self.mp.player.get_time(), force=True, transcribe=True)
        )
        clip_start_btn.pack(side=LEFT, fill=X, expand=YES)
        
        translate_btn = ttk.Button(
            master=container,
            text="当前片段翻译",
            # bootstyle=SECONDARY,
            padding=10,
            command=lambda: self.update_clip(self.mp.player.get_time(), force=True, translate=True)
        )
        translate_btn.pack(side=LEFT, fill=X, expand=YES)

        start_btn = ttk.Button(
            master=container,
            text="视频字幕生成",
            # bootstyle=SECONDARY,
            padding=10,
            command=self.on_video_transcribe
        )
        start_btn.pack(side=LEFT, fill=X, expand=YES)
        
        export_btn = ttk.Button(
            master=container,
            text="视频字幕导出",
            # bootstyle=SECONDARY,
            padding=10,
            command=self.export_srt
        )
        export_btn.pack(side=LEFT, fill=X, expand=YES)

        transcribe_pregress = ttk.Progressbar(
            master=container,
            bootstyle="success",
            maximum=1,
            variable=self.task_progress_value
        )
        transcribe_pregress.pack(side=LEFT, fill=X, expand=YES)

    def play(self, path=None):
        self.state.playing = True
        self.play_btn.configure(text=Emoji.get('double vertical bar'))
        self.mp.player.play(path)

    def pause(self):
        self.state.playing = False
        self.play_btn.configure(text=Emoji.get(
            'black right-pointing triangle'))
        self.mp.player.pause()

    def stop(self):
        self.state.playing = False
        self.mp.player.stop()
    
    def update_clip(self, play_time: float, force=False, translate=False, transcribe=False):
        curr_clip = self.srt_container.get_current_clip()
        if translate:
            curr_clip.target_text = self.agent.translate(curr_clip.source_text)
            LOGGER.debug(curr_clip.full_text())
        
        if transcribe:
            self.agent.tanscribe(curr_clip)

        # LOGGER.debug(play_time)
        if force or self.srt_container.update_current_clip(play_time):
            self.editor.load_clip(self.srt_container.get_current_clip())
            self.next_editor.load_clip(self.srt_container.get_current_next_clip())

    def on_play_button_click(self, e=None):
        if self.state.playing:
            self.pause()
        else:
            self.play()
    
    def on_open_file(self, type):
        if type == 'video':
            if self.state.playing:
                self.pause()
            self.config.video_path = filedialog.askopenfilename(title="选择视频文件", filetypes=[('Video File', '.mp4 .mkv')])
            self.agent.update_video_path()
            if self.agent.path_exists(self.agent.bi_srt_path):
                self.srt_container.load_srt(self.agent.bi_srt_path)
            self.play(self.config.video_path)
        elif type == 'srt':
            srt_path = filedialog.askopenfilename(title="选择字幕文件", filetypes=[('Srt File', '.srt')])
            self.srt_container.load_srt(srt_path)
            self.update_clip(self.mp.player.get_time(), force=True)
        else:
            assert False, f'invalid file type {type}'
    
    def on_video_transcribe(self):
        if not os.path.exists(self.config.video_path):
            LOGGER.warn(f"视频不存在 {self.config.video_path}")
            return

        if os.path.exists(self.agent.bi_srt_path):
            self.srt_container.load_srt(self.agent.bi_srt_path)
        else:
            self.agent.speech_to_text()
            self.agent.translate_srt()
            self.srt_container.load_srt(self.agent.bi_srt_path)

    def on_clip_nav(self, next=True, timeline=""):
        
        if self.state.playing:
            self.pause()

        if timeline != "":
            val = timeline_to_ms(timeline) / self.mp.player.get_length()
        elif next:
            val = self.srt_container.get_current_next_clip().get_start_time_ms() / self.mp.player.get_length()
        else:
            val = self.srt_container.get_current_prev_clip().get_start_time_ms() / self.mp.player.get_length()
        self.mp.on_progress(val, force=True)
        self.play()
    
    def export_srt(self):
        srt_text = self.srt_container.export_srt()
        filepath = filedialog.asksaveasfilename(filetypes=[("Srt File", ".srt")])
        if not filepath.endswith(".srt"):
            filepath += ".srt"
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(srt_text)

    def run(self):
        self.mainloop()
