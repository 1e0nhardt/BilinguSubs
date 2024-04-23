from pathlib import Path
from tkinter import ttk as tttk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.icons import Emoji
from PIL import Image, ImageTk

from src.subtitle_edit_app import SrtClip


class SubtitleEditor(ttk.Frame):

    def __init__(self, master) -> None:
        super().__init__(master)
        self.id_label = ttk.StringVar(value="12")
        self.time_label_start = ttk.StringVar(value="00:13:21:123")
        self.time_label_end = ttk.StringVar(value="00:13:23:123")

        container_left = ttk.Frame(master)
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
            textvariable=self.time_label_start
        )
        btn.pack(fill=X, expand=TRUE)
        
        btn = ttk.Button(
            container_left,
            textvariable=self.time_label_end
        )
        btn.pack(fill=X, expand=TRUE)

        img = Image.open('D:/MyTools/BilinguSubs/assets/bochi.png').resize((120, 120))
        self.img_tk = ImageTk.PhotoImage(img)

        img_label = ttk.Label(
            container_left, 
            image=self.img_tk,
        )
        img_label.pack(fill=BOTH, expand=YES)

        container_right = ttk.Frame(master)
        container_right.pack(side=LEFT, fill=X, expand=YES)

        self.text_editor = ttk.Text(container_right, height=10)
        self.text_editor.pack(fill=X, expand=TRUE)
        self.text_editor.insert(INSERT, "hello world")
        # self.text_editor.tag_add("good", 1.0, 2.0)  # 区域名："good"，区域：第一行第0列---->第2行第0列
        # self.text_editor.tag_config("good", background="yellow", foreground="red") #　设置"good"区域背景和前景颜色
        # self.text_editor.tag_bind("good", "<Button-1>", lambda e: print("hello world"))
    
    def load_clip(self, clip: SrtClip):
        self.id_label.set(clip.id)
        self.time_label_start.set(clip.start)
        self.time_label_end.set(clip.end)
        self.text_editor.delete(1.0, END)
        self.text_editor.insert(INSERT, clip.full_text())