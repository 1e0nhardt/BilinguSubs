import os
import time
import warnings
from dataclasses import dataclass

import tyro
import whisper
from deep_translator import BaiduTranslator, GoogleTranslator
from rich.console import Console
from rich.progress import Progress

from srt_assembler import SrtAssembler
from utils import LOGGER, ensure_folder_exists, extract_sound_from_video

warnings.filterwarnings('ignore')
CONSOLE = Console()

# Whisper模型默认的采样率
SAMPLE_RATE = 16000


@dataclass
class TaskConfig:
    """为输入视频生成双语字幕文件"""

    # 输入视频目录
    video_dir: str = 'assets/video/'
    # 音频目录
    audio_dir: str = 'assets/audio/'
    # 未翻译的字幕目录
    srt_dir: str = 'assets/srt/'
    # 模型：tiny | base | small | medium | large
    whisper_model: str = 'medium' 
    # 只用最后224个token会被使用。'Hello, welcome to my lecture.'可以减少无标点符号的情况。之后的部分建议写一些可能很难识别的专用名词。
    whisper_prompt: str = 'Hello, welcome to my lecture. And if a sentence is too long, break it at natural pauses. And this is a game dev video use Godot about Slay The Spire.'
    # 用逗号断句的句子长度阈值
    comma_as_end_threshold: int = 80
    # 只进行翻译(使用srt_dir中的.srt文件)
    only_translate: bool = False
    # 语音转文字+翻译(使用audio_dir中的.mp3, .wav文件)
    input_is_audio: bool = False
    # 翻译后只保留中文字幕
    only_zh: bool = False
    # 任务类型 transcribe | translate
    task: str = 'transcribe'
    # 使用百度api
    use_baidu_api: bool = False
    baidu_appid: str = ''
    baidu_appkey: str = ''
    # 翻译源语言
    src_lang: str = 'en'
    # 翻译目标语言
    tgt_lang: str = 'zh'


class GenerateSrtTask(object):
    def __init__(self, config: TaskConfig) -> None:
        self.config = config
        self.model = None
        self.progress = Progress(transient=True)

        self._video_names = list(filter(lambda s: s.endswith(('mp4', 'mkv')), os.listdir(config.video_dir)))
        if self.config.input_is_audio:
            self._video_names = list(filter(lambda s: s.endswith(('mp3', 'wav')), os.listdir(config.audio_dir)))
        if self.config.only_translate:
            self._video_names = list(filter(lambda s: s.endswith('srt'), os.listdir(config.srt_dir)))
    
    def execute(self):
        if (not self.config.only_translate) and (not self.config.input_is_audio): 
            CONSOLE.rule('提取音频')
            for v in self._video_names:
                self.extract_audio_from_video(v)
        
        if not self.config.only_translate:
            CONSOLE.rule('音频转文字')
            for v in self._video_names:
                self.speech_to_text(v)
        
        CONSOLE.rule('字幕翻译')
        
        for v in self._video_names:
            try:
                self.translate_srt(v)
            except Exception as e:
                LOGGER.warn(v +'翻译失败')
                LOGGER.error(e)

    def extract_audio_from_video(self, basename: str):
        filename, suffix = os.path.splitext(basename)
        video_path = self.config.video_dir + basename
        audio_path = self.config.audio_dir + filename + '.mp3'

        if os.path.exists(audio_path):
            LOGGER.info(audio_path + ' 已存在')
            return
        
        with CONSOLE.status(filename + ' 提取中'):
            extract_sound_from_video(video_path, audio_path, format='mp3')
        LOGGER.info(filename + ' 提取完成')

    def speech_to_text(self, basename):
        filename, suffix = os.path.splitext(basename)
        
        audio_path = self.config.audio_dir + filename + '.mp3'
        srt_path = self.config.srt_dir + filename + '.srt'

        if os.path.exists(srt_path):
            LOGGER.info(srt_path + ' 已存在')
            return
        
        if not self.model:
            with CONSOLE.status('模型加载中...'):
                self.model = whisper.load_model(self.config.whisper_model)
        
        whisper_task = self.progress.add_task(f'[green]{filename} 转文本中...\n', total=100)
        self.progress.start()

        # 将音频读取为numpy
        audio_np = whisper.audio.load_audio(audio_path)

        # 选取长5分钟的片段
        clip_start = 0
        clip_end = clip_start + 5 * 60 * SAMPLE_RATE
        clip_last_sentence = ''

        # 逐片段转文本
        sa = SrtAssembler(self.config.comma_as_end_threshold)
        while clip_end < audio_np.size:
            result = self.model.transcribe(audio_np[clip_start:clip_end], word_timestamps=True, initial_prompt=self.config.whisper_prompt + ' ' + clip_last_sentence, task=self.config.task)
                
            for segment in result['segments']:
                for word_dict in segment['words']:
                    sa.get_next_input(word_dict, clip_start / SAMPLE_RATE)
            
            clip_start, clip_last_sentence = sa.get_clip_end_info(SAMPLE_RATE)
            clip_end = clip_start + 5 * 60 * SAMPLE_RATE

            self.progress.update(whisper_task, advance=(clip_end - clip_start)/audio_np.size*100)
        else:
            result = self.model.transcribe(audio_np[clip_start:], word_timestamps=True, initial_prompt=self.config.whisper_prompt + ' ' + clip_last_sentence, task=self.config.task)

            for segment in result['segments']:
                for word_dict in segment['words']:
                    sa.get_next_input(word_dict, clip_start / SAMPLE_RATE)
            
            self.progress.update(whisper_task, completed=100)
            self.progress.stop()

        LOGGER.info(filename + ' 转换完成')

        sa.generate_srt(srt_path)

    def translate_srt(self, basename):
        filename, suffix = os.path.splitext(basename)

        srt_path = self.config.srt_dir + filename + '.srt'
        if (not self.config.only_translate) and (not self.config.input_is_audio):
            bilingual_srt_path = self.config.video_dir + filename + '_zh&en.srt'
        else:
            bilingual_srt_path = self.config.srt_dir + filename + '_zh&en.srt'

        if os.path.exists(bilingual_srt_path):
            LOGGER.info(bilingual_srt_path + ' 已存在')
            return
        
        with CONSOLE.status(filename + ' 翻译中', spinner='earth'):
            if self.config.use_baidu_api:
                translator = BaiduTranslator(
                    source=self.config.src_lang, target=self.config.tgt_lang, 
                    appid=self.config.baidu_appid, appkey=self.config.baidu_appkey
                )
            else:
                if self.config.tgt_lang == 'zh':
                    self.config.tgt_lang = 'zh-CN'
                # 有最多5000字符限制
                translator = GoogleTranslator(source=self.config.src_lang, target=self.config.tgt_lang)

            subtitles = []
            translated_subtitles = []
            total_chara = 0
            with open(srt_path, 'r', encoding='utf-8') as f:
                text_lines = f.readlines()
                for i in range(2, len(text_lines) - 1, 4):
                    subtitle = text_lines[i]
                    total_chara += len(subtitle)
                    subtitles.append(text_lines[i])
                    if total_chara > 4500:
                        translation = translator.translate(''.join(subtitles))
                        translated_subtitles.extend(translation.split('\n'))
                        subtitles = []
                        total_chara = 0
                        time.sleep(.2) # 等待0.2秒

                translation = translator.translate(''.join(subtitles))
                translated_subtitles.extend(translation.split('\n'))

            for i in range(2, len(text_lines) - 1, 4):
                if self.config.only_zh:
                    text_lines[i] = translated_subtitles[(i - 2) // 4] + '\n' # 单独中文字幕
                else:
                    text_lines[i] = translated_subtitles[(i - 2) // 4] + '\n' + text_lines[i] # 中英混合

            with open(bilingual_srt_path, 'w', encoding='utf-8') as f:
                f.write(''.join(text_lines))

        LOGGER.info(filename + ' 翻译完成')

if __name__ == '__main__':
    args = tyro.cli(TaskConfig)

    ensure_dir_end_with_slash = lambda s: s if s.endswith('/') else (s + '/')
    args.video_dir = ensure_dir_end_with_slash(args.video_dir)
    args.audio_dir = ensure_dir_end_with_slash(args.audio_dir)
    args.srt_dir = ensure_dir_end_with_slash(args.srt_dir)
    ensure_folder_exists(args.audio_dir)
    ensure_folder_exists(args.srt_dir)

    if args.task == 'translate':
        LOGGER.warn('Word-level timestamps on translations may not be reliable.(结果时间轴可能不准)')

    task = GenerateSrtTask(args)

    task.execute()
