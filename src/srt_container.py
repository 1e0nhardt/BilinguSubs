import os

from utils import LOGGER

class SrtClip(object):

    def __init__(self) -> None:
        self.id = 0
        self.start = ""
        self.end = ""
        self.source_text = ""
        self.target_text = ""
    
    def set_id(self, id: int):
        self.id = id
    
    def set_time_range(self, time_line:str):
        if time_line.find("-->") == -1:
            LOGGER.error(f"时间戳格式不合法！ {time_line}")
        self.start, self.end = time_line.split("-->")
    
    def set_text(self, text: str):
        splits = text.strip().splitlines()
        if len(splits) == 1:
            self.source_text = text
        elif len(splits) == 2:
            self.source_text, self.target_text = splits
        else:
            self.source_text = text
            LOGGER.warn(f"异常字幕数据: {text}")
    
    def get_end_time_ms(self):
        return self.timeline_to_ms(self.end)
    
    def time_in_clip(self, ptime):
        return ptime > self.timeline_to_ms(self.start) and ptime < self.get_end_time_ms()
    
    def full_text(self):
        return self.source_text + "\n" + self.target_text

    def update_text(self, all_text: str):
        splits = all_text.strip().splitlines()
        if len(splits) == 2:
            self.source_text, self.target_text = splits
        else:
            self.source_text = all_text
            LOGGER.warn(f"异常字幕数据: {all_text}")
    
    def timeline_to_ms(self, timeline: str):
        hrs, mins, sec_ms = timeline.strip().split(':')
        seconds, ms = sec_ms.split(",")
        return (int(hrs) * 60 * 60 + int(mins) * 60 + int(seconds)) * 1000 + int(ms)


class SrtContainer(object):

    def __init__(self) -> None:
        self.clips = []
        self.current_index = -1
    
    def get_current_clip(self) -> SrtClip:
        return self.clips[self.current_index]

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
        if not os.path.isfile(path):
            LOGGER.error(f"字幕加载失败，路径{path}不存在")
            return

        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        clip = SrtClip()
        all_text = []
        for line in lines:
            line = line.strip()

            if line.isdigit():
                clip.set_id(int(line))
                if len(all_text) > 0:
                    clip.set_text("\n".join(all_text))
                    self.clips.append(clip)
                    clip = SrtClip()
                    all_text = []
                    
            elif line.find("-->") != -1:
                clip.set_time_range(line)
            elif line != "":
                all_text.append(line)
        clip.set_text("\n".join(all_text))
        self.current_index = 0
            
    def export_srt(self):
        pass
