import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from src.vlc_player import VlcPlayer

from utils import LOGGER

class MediaPlayer(ttk.Frame):

    def __init__(self, master, *args):
        super().__init__(master)
        self.app = master
        self.player = VlcPlayer(*args)
        self.pack(fill=BOTH, expand=YES)
        
        self.scale_pressed = False

        self.create_media_window()
        self.create_progress_meter()
    
    def reload_for_ass(self, path):
        LOGGER.error("Just Can't Work Properly!")
        return
        LOGGER.debug("RELOAD FOR ASS")
        self.player.reload_ass(path)
        self.player.play()

    def create_media_window(self):
        """Create frame to contain media"""
        self._canvas = ttk.Canvas(self, bg="black", width=1280, height=720)
        self._canvas.pack(fill=BOTH, expand=YES)
        self.player.set_window(self._canvas.winfo_id())

    def create_progress_meter(self):
        """Create frame with progress meter with lables"""
        container = ttk.Frame(self)
        container.pack(fill=X, expand=YES, pady=10)

        self.scale = ttk.Scale(
            master=container, 
            command=self.on_progress, 
            bootstyle=SECONDARY
        )
        self.scale.bind("<B1-Motion>", self.on_b1_motion)
        self.scale.bind("<ButtonRelease-1>", self.on_button_release_1)
        self.player.add_update_callback(self.on_player_update)
        self.scale.pack(side=LEFT, fill=X, expand=YES)

        self.time_label = ttk.Label(container, text='00:00')
        self.time_label.pack(side=LEFT, fill=X, padx=10)
    
    def update_time_labels(self, val):
        """Update progress labels when the scale is updated."""
        total = int(self.player.get_length() / 1000)

        elapse = int(float(val) * total)
        elapse_min = elapse // 60
        elapse_sec = elapse % 60
        elapse_hrs = elapse_min // 60
        elapse_min = elapse_min % 60

        total_min = total // 60
        total_sec = total % 60
        total_hrs = total_min // 60
        if total_hrs > 0:
            total_min = total_min % 60
            final_text = f'{elapse_hrs}:{elapse_min:02d}:{elapse_sec:02d}/{total_hrs:02d}:{total_min:02d}:{total_sec:02d}'
        else:
            final_text = f'{elapse_min:02d}:{elapse_sec:02d}/{total_min:02d}:{total_sec:02d}'
        
        self.time_label.configure(text=final_text)

    def on_b1_motion(self, event):
        self.scale_pressed = True
    
    def on_button_release_1(self, event):
        #TODO 识别scale最后一次更新，即拖动完释放的时间点。
        self.scale_pressed = False
    
    def set_progress(self, val: float):
        if self.scale_pressed:
            return
            
        self.update_time_labels(val)
        self.scale.set(val)

    def on_progress(self, val: float, force=False):
        if (not force) and (not self.scale_pressed):
            return
            
        print(f"Set Position {val} after")
        self.update_time_labels(val)
        self.player.set_position(val)
        self.app.update_clip(self.player.get_time())
    
    def on_player_update(self, event):
        self.set_progress(self.player.get_position())
        self.app.update_clip(self.player.get_time())

