import logging
import os

from pydub import AudioSegment
from rich.logging import RichHandler
from rich.traceback import install

from srt_assembler import SrtAssembler


class MyFilter(logging.Filter):
    def __init__(self, name: str = "") -> None:
        super().__init__(name)
        self.pys = []  # 记录项目所有的py文件
        for _, _, i in os.walk(os.path.dirname(__file__)):
            self.pys.extend([j for j in i if j.endswith('py')])
        # CONSOLE.print(self.pys)

    def filter(self, record):
        if record.filename in self.pys:
            return True
        return False
    
FORMAT = "%(message)s"
rich_handler = RichHandler(markup=True)
rich_handler.addFilter(MyFilter())
logging.basicConfig(
    level=logging.DEBUG, format=FORMAT, datefmt="[%X]", handlers=[rich_handler])

LOGGER = logging.getLogger("rich")

install(show_locals=False)


def ensure_folder_exists(path: str):
    if not os.path.exists(path):
        LOGGER.info(f'[red]Directory {path} does not exist, creating...[/]')
        os.makedirs(path, exist_ok=True)


# 从视频文件提取音轨
def extract_sound_from_video(video_path, sound_save_path, format='wav'):
    AudioSegment.from_file(video_path).export(sound_save_path, format=format)


def generate_srt(result, srt_path):
    srt_assembler = SrtAssembler()

    for segment in result['segments']:
        for word_dict in segment['words']:
            srt_assembler.get_next_input(word_dict)

    srt_assembler.generate_srt(srt_path)
