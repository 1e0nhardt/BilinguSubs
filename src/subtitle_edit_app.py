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
from utils import LOGGER

@dataclass
class AppState:

    playing: bool = False


class Application(ttk.Window):

    def __init__(self, title, theme_name='yeti', **args) -> None:
        super().__init__(title, theme_name, **args)
        self.state = AppState()
        self.config = AppConfig()
        self.srt_container = SrtContainer()
        self.srt_container.load_srt(self.config.srt_dir + "Creating a Cozy Pixel Campfire for a Roguelike Deckbuilder (S02E07).srt")
        self.agent = WhisperAgent(self.config)
        self.task_progress_value = ttk.DoubleVar()

        self.hdr_var = ttk.StringVar()
        # self.create_header()
        self.mp = MediaPlayer(self)
        self.create_buttonbox()
        self.editor = SubtitleEditor(self)
        self.play(self.config.video_path)

        self.editor.load_clip(self.srt_container.get_current_clip())

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
        
        clip_start_btn = ttk.Button(
            master=container,
            text="当前片段生成",
            # bootstyle=SECONDARY,
            padding=10,
            command=lambda: self.task_progress_value.set(self.task_progress_value.get() + 0.1)
        )
        clip_start_btn.pack(side=LEFT, fill=X, expand=YES)
        
        translate_btn = ttk.Button(
            master=container,
            text="当前片段翻译",
            # bootstyle=SECONDARY,
            padding=10,
            command=lambda: self.task_progress_value.set(self.task_progress_value.get() + 0.1)
        )
        translate_btn.pack(side=LEFT, fill=X, expand=YES)

        start_btn = ttk.Button(
            master=container,
            text="视频字幕生成",
            # bootstyle=SECONDARY,
            padding=10,
            command=lambda: self.task_progress_value.set(self.task_progress_value.get() + 0.1)
        )
        start_btn.pack(side=LEFT, fill=X, expand=YES)

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
    
    def update_clip(self, play_time: float):
        LOGGER.debug(play_time)
        if self.srt_container.update_current_clip(play_time):
            self.editor.load_clip(self.srt_container.get_current_clip())

    def on_play_button_click(self):
        if self.state.playing:
            self.pause()
        else:
            self.play()
    
    def on_open_file(self, type):
        if type == 'video':
            self.pause()
            self.config.video_path = filedialog.askopenfilename(title="选择视频文件", filetypes=[('Video File', '.mp4 .mkv')])
            self.play(self.config.video_path)
        elif type == 'srt':
            self.config.srt_path = filedialog.askopenfilename(title="选择字幕文件", filetypes=[('Srt File', '.srt')])
        else:
            assert False, f'invalid file type {type}'

    def run(self):
        self.mainloop()
