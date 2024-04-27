import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from src.srt_container import Clip
from utils import LOGGER

class SubtitleEditor(ttk.Frame):

    def __init__(self, master, next=False) -> None:
        super().__init__(master)
        self.app = master
        self.is_next = next
        self.id_label = ttk.StringVar(value="12")
        self.time_label_start = ttk.StringVar(value="00:13:21:123")
        self.time_label_end = ttk.StringVar(value="00:13:23:123")

        container = ttk.Frame(master)
        container.pack(fill=X, expand=True)
        container_left = ttk.Frame(container)
        container_left.pack(side=LEFT, fill=X)
        id_label = ttk.Label(
            container_left,
            justify=CENTER,
            font='-size 14',
            textvariable=self.id_label
        )
        id_label.pack()

        ttk.Style().configure('TButton', font="-size 10")
        btn = ttk.Button(
            container_left,
            textvariable=self.time_label_start,
            command=lambda: self.app.on_clip_nav(timeline=self.time_label_start.get())
        )
        btn.pack(fill=X, expand=TRUE)
        
        btn = ttk.Button(
            container_left,
            textvariable=self.time_label_end,
            command=lambda: self.app.on_clip_nav(timeline=self.time_label_end.get())
        )
        btn.pack(fill=X, expand=TRUE)

        container_right = ttk.Frame(container)
        container_right.pack(side=LEFT, fill=X, expand=YES)

        self.text_editor = ttk.Text(
            container_right, 
            height=5,
            font="-size 12"
        )
        # self.text_editor.insert(INSERT, "hello world")
        self.text_editor.pack(fill=X, expand=TRUE)
        self.text_editor.bind("<Key>", self.on_text_changed)
        # self.text_editor.tag_add("good", 1.0, 2.0)  # 区域名："good"，区域：第一行第0列---->第2行第0列
        # self.text_editor.tag_config("good", background="yellow", foreground="red") #　设置"good"区域背景和前景颜色
        # self.text_editor.tag_bind("good", "<Button-1>", lambda e: print("hello world"))
    
    def load_clip(self, clip: Clip):
        if clip is None:
            return
            
        self.id_label.set(clip.id)
        self.time_label_start.set(clip.start)
        self.time_label_end.set(clip.end)
        self.text_editor.delete(1.0, END)
        full_text = clip.full_text()
        if clip.type == 'ass':
            full_text = clip.style['Style'] + '\n' + full_text
        self.text_editor.insert(INSERT, full_text)
    
    def insert_text(self, text):
        self.text_editor.index(END, "\n" + text)
    
    def on_text_changed(self, e):
        if self.app.subtitle_container.is_empty():
            return

        LOGGER.debug(f"KeyTyped {e.char}")
        if self.is_next:
            self.app.subtitle_container.get_current_next_clip().update_text(self.text_editor.get(0.0, END))
        else:
            self.app.subtitle_container.get_current_clip().update_text(self.text_editor.get(0.0, END))