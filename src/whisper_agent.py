import os
import time
import warnings

import whisper
from deep_translator import BaiduTranslator, GoogleTranslator
from rich.console import Console

from srt_assembler import SrtAssembler
from src.config import AppConfig
from src.srt_container import SrtClip
from utils import LOGGER, ensure_folder_exists, extract_sound_from_video

warnings.filterwarnings('ignore')
CONSOLE = Console()

# Whisper模型默认的采样率
SAMPLE_RATE = 16000


class WhisperAgent(object):

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.model = None
        self.audio_np = None

        self.update_video_path()

        if self.config.use_baidu_api:
            self.translator = BaiduTranslator(
                source=self.config.src_lang, target=self.config.tgt_lang, 
                appid=self.config.baidu_appid, appkey=self.config.baidu_appkey
            )
        else:
            if self.config.tgt_lang == 'zh':
                self.config.tgt_lang = 'zh-CN'
            # 有最多5000字符限制
            self.translator = GoogleTranslator(source=self.config.src_lang, target=self.config.tgt_lang)
    
    def translate(self, text):
        return self.translator.translate(text)
    
    def tanscribe(self, clip: SrtClip):
        if not self.model:
            with CONSOLE.status('模型加载中...'):
                self.model = whisper.load_model(self.config.whisper_model)
        
        self.prepare_audio()
        
        clip_start = int(clip.get_start_time_ms() / 1000 * SAMPLE_RATE)
        clip_end = int((clip.get_end_time_ms()) / 1000 * SAMPLE_RATE)

        result = self.model.transcribe(self.audio_np[clip_start:clip_end], word_timestamps=True, initial_prompt=self.config.whisper_prompt, task=self.config.task)

        transcribe_text = ""
        for segment in result['segments']:
            for word_dict in segment['words']:
                transcribe_text += (word_dict['word'])

        clip.source_text = transcribe_text
        clip.target_text = self.translate(transcribe_text)

    def extract_audio_from_video(self):
        if self.path_exists(self.audio_path):
            return
        
        extract_sound_from_video(self.config.video_path, self.audio_path, format='mp3')

    def speech_to_text(self):
        if self.path_exists(self.srt_path):
            return
        
        if not self.model:
            with CONSOLE.status('模型加载中...'):
                self.model = whisper.load_model(self.config.whisper_model)

        # 将音频读取为numpy
        # self.audio_np = whisper.audio.load_audio(self.audio_path)
        self.prepare_audio()

        # 选取长6分钟的片段
        clip_start = 0
        clip_end = clip_start + 6 * 60 * SAMPLE_RATE
        clip_last_sentence = ''

        # 逐片段转文本
        sa = SrtAssembler(self.config.comma_as_end_threshold)
        while clip_end < self.audio_np.size:
            result = self.model.transcribe(self.audio_np[clip_start:clip_end], word_timestamps=True, initial_prompt=self.config.whisper_prompt + ' ' + clip_last_sentence, task=self.config.task)
                
            for segment in result['segments']:
                for word_dict in segment['words']:
                    sa.get_next_input(word_dict, clip_start / SAMPLE_RATE)
            
            clip_start, clip_last_sentence = sa.get_clip_end_info(SAMPLE_RATE)
            clip_end = clip_start + 6 * 60 * SAMPLE_RATE
        else:
            result = self.model.transcribe(self.audio_np[clip_start:], word_timestamps=True, initial_prompt=self.config.whisper_prompt + ' ' + clip_last_sentence, task=self.config.task)

            for segment in result['segments']:
                for word_dict in segment['words']:
                    sa.get_next_input(word_dict, clip_start / SAMPLE_RATE)
            
        sa.generate_srt(self.srt_path)
    
    def translate_srt(self):
        if self.path_exists(self.bi_srt_path):
            return

        subtitles = []
        translated_subtitles = []
        total_chara = 0
        with open(self.srt_path, 'r', encoding='utf-8') as f:
            text_lines = f.readlines()
            for i in range(2, len(text_lines) - 1, 4):
                subtitle = text_lines[i]
                total_chara += len(subtitle)
                subtitles.append(text_lines[i])
                if total_chara > self.config.api_character_limit:
                    translation = self.translator.translate(''.join(subtitles))
                    translated_subtitles.extend(translation.split('\n'))
                    subtitles = []
                    total_chara = 0
                    time.sleep(.2) # 等待0.2秒

            translation = self.translator.translate(''.join(subtitles))
            translated_subtitles.extend(translation.split('\n'))

        for i in range(2, len(text_lines) - 1, 4):
            if self.config.only_zh:
                text_lines[i] = translated_subtitles[(i - 2) // 4] + '\n' # 单独中文字幕
            else:
                text_lines[i] = translated_subtitles[(i - 2) // 4] + '\n' + text_lines[i] # 中英混合

        with open(self.bi_srt_path, 'w', encoding='utf-8') as f:
            f.write(''.join(text_lines))

    def path_exists(self, path):
        if os.path.exists(path):
            LOGGER.info(path + ' 已存在')
            return True
        return False
    
    def update_video_path(self):
        path = self.config.video_path
        LOGGER.debug(path)
        filename, suffix = os.path.splitext(os.path.basename(path))
        ensure_folder_exists(self.config.audio_dir)
        ensure_folder_exists(self.config.srt_dir)
        self.audio_path = self.config.audio_dir + filename + '.mp3'
        self.srt_path = self.config.srt_dir + filename + '_en.srt'
        self.bi_srt_path = self.config.srt_dir + filename + '.srt'
        LOGGER.info(f'AudioPath: {self.audio_path}')
        LOGGER.info(f'SrtPath: {self.srt_path}')

        self.audio_np = None
    
    def prepare_audio(self):
        if self.audio_np is not None:
            return
        
        if not self.path_exists(self.audio_path):
            LOGGER.info("提取音频中...")
            self.extract_audio_from_video()
            LOGGER.info("提取音频完成")
        
        self.audio_np = whisper.audio.load_audio(self.audio_path)
        

