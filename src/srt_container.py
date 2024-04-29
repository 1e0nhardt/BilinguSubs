import os

from utils import LOGGER, timestring_to_ms

class Clip(object):

    def __init__(self, valid_style_names=[]) -> None:
        if valid_style_names:
            self.valid_style_names = valid_style_names
        else:
            self.valid_style_names = []

        self.id = 0
        self.start = ""
        self.end = ""
        self.source_text = ""
        self.target_text = ""
        self.style = {}
        self.type = 'srt'
        self.next_clips = [] # 重新transcribe大段语句时使用。

    def is_style_validate(self, style_name):
        if len(self.valid_style_names) == 0:
            return
        return style_name in self.valid_style_names
    
    def set_id(self, id: int):
        self.id = id
    
    def set_time_range(self, time_line:str):
        if time_line.find("-->") == -1:
            LOGGER.error(f"时间戳格式不合法！ {time_line}")
        splits = time_line.split("-->")
        self.start = splits[0].strip()
        self.end = splits[1].strip()

    def set_text(self, text: str):
        splits = text.strip().splitlines()
        if len(splits) == 1:
            self.source_text = text
        elif len(splits) == 2:
            self.source_text, self.target_text = splits
        else:
            self.source_text = text
            LOGGER.warn(f"异常字幕数据: {text}")
    
    def get_ass_timeline(self, t):
        """1234.12 -> xx:xx:xx,xxx (h:m:s,ms)"""
        seconds = int(t)
        ms = round(t - seconds, 3)
        ms = f'{ms:.2f}'[2:]
        minutes = seconds // 60
        seconds %= 60
        hours = minutes // 60
        minutes %= 60
        return f'{hours:02d}:{minutes:02d}:{seconds:02d}.{ms}'
    
    def get_start_time_ms(self):
        return timestring_to_ms(self.start, self.type == 'ass')

    def get_end_time_ms(self):
        return timestring_to_ms(self.end, self.type == 'ass')
    
    def time_in_clip(self, ptime):
        return ptime > self.get_start_time_ms() and ptime < self.get_end_time_ms()
    
    def full_text(self):
        return self.source_text + "\n" + self.target_text

    def update_text(self, all_text: str):
        splits = all_text.strip().splitlines()
        if self.type == 'srt':
            if len(splits) == 2:
                self.source_text, self.target_text = splits
            else:
                self.source_text = all_text
                LOGGER.info(f"非双语字幕数据: {all_text}")
        else:
            if len(splits) == 3:
                self.style['Style'], self.source_text, self.target_text = splits
            elif len(splits) == 2:
                self.style['Style'], self.source_text = splits
                LOGGER.info(f"非双语字幕数据: {all_text}")
            else:
                self.source_text = all_text
                LOGGER.warn(f'ass 字幕格式错误 {all_text}')


class SrtContainer(object):

    def __init__(self) -> None:
        self.clips = []
        self.current_index = -1

    def is_empty(self) -> bool:
        return len(self.clips) == 0
    
    def get_current_clip(self) -> Clip:
        if len(self.clips) == 0:
            return
        return self.clips[self.current_index]

    def get_current_prev_clip(self) -> Clip:
        if self.current_index == 0:
            return None
        return self.clips[self.current_index - 1]

    def get_current_next_clip(self) -> Clip:
        if self.current_index + 2 > len(self.clips):
            return None
        return self.clips[self.current_index + 1]

    def udpate_current_clip(self, new_text):
        self.clips[self.current_index].update_text(new_text)

    def get_timeline(self, t):
        """1234.12 -> xx:xx:xx,xxx (h:m:s,ms)"""
        seconds = int(t)
        ms = round(t - seconds, 3)
        ms = f'{ms:.3f}'[2:]
        minutes = seconds // 60
        seconds %= 60
        hours = minutes // 60
        minutes %= 60
        return f'{hours:02d}:{minutes:02d}:{seconds:02d},{ms}'
    
    def update_current_clip(self, play_time: float) -> bool:
        if self.get_current_clip() is None:
            return 

        if self.get_current_clip().time_in_clip(play_time):
            return False
        
        if self.clips[self.current_index + 1].time_in_clip(play_time):
            self.current_index += 1
        else:
            for i in range(len(self.clips)):
                if self.clips[i].get_end_time_ms() > play_time:
                    break
            self.current_index = i
        
        return True

    def load_srt(self, path):
        self.clips.clear()
        if not os.path.isfile(path):
            LOGGER.error(f"字幕加载失败，路径{path}不存在")
            return

        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        clip = Clip()
        all_text = []
        for line in lines:
            line = line.strip()

            if line.isdigit():
                if len(all_text) > 0:
                    clip.set_text("\n".join(all_text))
                    self.clips.append(clip)
                    clip = Clip()
                    clip.set_id(int(line))
                    all_text = []
                else: # 第一条
                    clip.set_id(int(line))
                    
            elif line.find("-->") != -1:
                clip.set_time_range(line)
            elif line != "":
                all_text.append(line)
        clip.set_text("\n".join(all_text))
        self.current_index = 0
            
    def export_srt(self):
        srt_text = ""
        for clip in self.clips:
            srt_text += f"{clip.id}\n"
            srt_text += f"{clip.start} --> {clip.end}\n"
            srt_text += f"{clip.source_text.strip()}\n"
            srt_text += f"{clip.target_text.strip()}\n"
            srt_text += "\n"
        
        return srt_text
