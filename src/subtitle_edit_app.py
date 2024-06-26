from dataclasses import dataclass
from functools import partial
import os
import subprocess

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.icons import Emoji
from tkinter import filedialog, dialog

from src.srt_container import SrtContainer
from src.ass_container import AssContainer
from src.video_player import MediaPlayer
from src.subtitle_editor import SubtitleEditor
from src.config import AppConfig
from src.whisper_agent import WhisperAgent
from utils import LOGGER, timestring_to_ms


@dataclass
class AppState:

    playing: bool = False
    use_ass: bool = False


class Application(ttk.Window):

    def __init__(self, title, theme_name='yeti', **args) -> None:
        super().__init__(title, theme_name, **args)
        self.state = AppState()
        self.config = AppConfig()
        self.agent = WhisperAgent(self.config)
        self.subtitle_container = None
        self.mp = None
        self.task_progress_value = ttk.DoubleVar()

        self.hdr_var = ttk.StringVar()
        # self.create_header()
        # self.mp = MediaPlayer(self)
        self.mp = MediaPlayer(self, f'--sub-file={self.agent.bi_srt_path}')
        self.create_buttonbox()
        self.replace_words_editor = ttk.Text(
            self, 
            height=1,
            font="-size 12"
        )
        self.replace_words_editor.insert(INSERT, "戈多:Godot;")
        self.replace_words_editor.pack(fill=X, expand=TRUE)
        self.prev_editor = SubtitleEditor(self, prev=True)
        self.editor = SubtitleEditor(self)
        self.next_editor = SubtitleEditor(self, next=True)

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

        translate_btn = ttk.Button(
            master=container,
            text="删除前一个片段",
            # bootstyle=SECONDARY,
            padding=10,
            command=self.delete_prev_clip
        )
        translate_btn.pack(side=LEFT, fill=X, expand=YES)

        translate_btn = ttk.Button(
            master=container,
            text="延长当前片段时间轴",
            # bootstyle=SECONDARY,
            padding=10,
            command=self.clip_timeline_adjust
        )
        translate_btn.pack(side=LEFT, fill=X, expand=YES)

        translate_btn = ttk.Button(
            master=container,
            text="合并两个片段",
            # bootstyle=SECONDARY,
            padding=10,
            command=self.combine_two_clip
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
        self.bind('<Control-s>', self.save_srt)
        
        export_btn = ttk.Button(
            master=container,
            text="常见错误词语替换",
            # bootstyle=SECONDARY,
            padding=10,
            command=self.replace_wrong_words
        )
        export_btn.pack(side=LEFT, fill=X, expand=YES)

        self.combine_btn = ttk.Button(
            master=container,
            text="渲染硬字幕",
            # bootstyle=SECONDARY,
            padding=10,
            command=self.on_export_mkv
        )
        self.combine_btn.pack(side=LEFT, fill=X, expand=YES)

        # transcribe_pregress = ttk.Progressbar(
        #     master=container,
        #     bootstyle="success",
        #     maximum=1,
        #     variable=self.task_progress_value
        # )
        # transcribe_pregress.pack(side=LEFT, fill=X, expand=YES)

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
        curr_clip = self.subtitle_container.get_current_clip()
        if translate:
            curr_clip.target_text = self.agent.translate(curr_clip.source_text)
        
        if transcribe:
            self.agent.tanscribe(curr_clip)
            self.subtitle_container.update_clip_and_next_clips()
            force = True

        # LOGGER.debug(play_time)
        if force or self.subtitle_container.update_current_clip(play_time):
            self.prev_editor.load_clip(self.subtitle_container.get_current_prev_clip())
            self.editor.load_clip(self.subtitle_container.get_current_clip())
            self.next_editor.load_clip(self.subtitle_container.get_current_next_clip())
    
    def replace_wrong_words(self):
        # k:v;
        text = self.replace_words_editor.get(0.0, END)
        splits = text.split(';')
        replace_dict = {}
        for s in splits:
            k, v = s.split(':')
            replace_dict[k.strip()] = v.strip() 
        self.prev_editor.replace_wrong_words(replace_dict)
        self.editor.replace_wrong_words(replace_dict)
        self.next_editor.replace_wrong_words(replace_dict)

    def on_play_button_click(self, e=None):
        if isinstance(self.focus_get(), ttk.Text):
            return

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
                self.load_srt(self.agent.bi_srt_path)
            self.play(self.config.video_path)
        elif type == 'srt':
            srt_path = filedialog.askopenfilename(title="选择字幕文件", filetypes=[('Srt File', '.srt .ass')])
            self.load_srt(srt_path)
            self.update_clip(self.mp.player.get_time(), force=True)
        else:
            assert False, f'invalid file type {type}'
    
    def on_video_transcribe(self):
        if not os.path.exists(self.config.video_path):
            LOGGER.warn(f"视频不存在 {self.config.video_path}")
            return

        if os.path.exists(self.agent.bi_srt_path):
            self.subtitle_container.load_srt(self.agent.bi_srt_path)
        else:
            self.agent.speech_to_text()
            self.agent.translate_srt()
            self.subtitle_container.load_srt(self.agent.bi_srt_path)

    def on_clip_nav(self, next=True, timeline=""):
        
        if self.state.playing:
            self.pause()

        if timeline != "":
            val = timestring_to_ms(timeline, self.state.use_ass) / self.mp.player.get_length()
        elif next:
            val = self.subtitle_container.get_current_next_clip().get_start_time_ms() / self.mp.player.get_length()
        else:
            val = self.subtitle_container.get_current_prev_clip().get_start_time_ms() / self.mp.player.get_length()
        self.mp.on_progress(val, force=True)
        self.play()
    
    def combine_two_clip(self):
        if self.state.playing:
            self.pause()
        cur_clip = self.subtitle_container.get_current_clip()
        next_clip = self.subtitle_container.get_current_next_clip()
        cur_clip.source_text += next_clip.source_text
        cur_clip.target_text += next_clip.target_text
        cur_clip.end = next_clip.end
        self.subtitle_container.remove_next_clip()
        self.update_clip(self.mp.player.get_time(), force=True)
    
    def delete_prev_clip(self):
        if self.state.playing:
            self.pause()
        self.subtitle_container.remove_prev_clip()
        self.update_clip(self.mp.player.get_time(), force=True)

    def clip_timeline_adjust(self):
        if self.state.playing:
            self.pause()
        cur_clip = self.subtitle_container.get_current_clip()
        next_clip = self.subtitle_container.get_current_next_clip()
        cur_clip.end = next_clip.start
        self.update_clip(self.mp.player.get_time(), force=True)

    def on_export_mkv(self):
        if self.state.playing:
            self.pause()
        srt_text = self.subtitle_container.export_srt()
        with open(self.agent.bi_srt_path, 'w', encoding='utf-8') as f:
            f.write(srt_text)
        subprocess.run(
            f"ffmpeg -i \"{self.config.video_path}\" -vf subtitles=\"{self.agent.bi_srt_path}\" \"{self.config.mkv_dir + os.path.basename(self.config.video_path)}\""
        )

    def load_srt(self, path: str):
        if path.endswith('.srt'):
            LOGGER.info(f'{path} SRT加载成功')
            self.subtitle_container = SrtContainer()
            self.state.use_ass = False
        else:
            LOGGER.info(f'{path} ASS加载成功')
            self.subtitle_container = AssContainer()
            self.state.use_ass = True
            # if self.mp:
            #     self.mp.reload_for_ass(path)
                # self.play(self.config.video_path)
        self.subtitle_container.load_srt(path)        

    def export_srt(self):
        srt_text = self.subtitle_container.export_srt()
        filepath = filedialog.asksaveasfilename(filetypes=[("Srt File", ".srt .ass")])
        if isinstance(self.subtitle_container, AssContainer):
            if not filepath.endswith(".ass"):
                filepath += ".ass"
        else:
            if not filepath.endswith(".srt"):
                filepath += '.srt'

        LOGGER.info(f'{filepath} 保存成功')
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(srt_text)
    
    def save_srt(self, e):
        srt_text = self.subtitle_container.export_srt()
        with open(self.agent.bi_srt_path, 'w', encoding='utf-8') as f:
            f.write(srt_text)
        LOGGER.info(f'{self.agent.bi_srt_path} 保存成功')

    def run(self):
        self.mainloop()
