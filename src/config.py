from dataclasses import dataclass

@dataclass
class AppConfig:
    video_path: str = "assets/video/sts.mp4"
    audio_dir: str = "assets/audio/"
    srt_dir: str = "assets/srt/"
    # 模型：tiny | base | small | medium | large | downloaded_model_path
    whisper_model: str = 'medium' 
    # 只有最后224个token会被使用。'Hello, welcome to my lecture.'可以减少无标点符号的情况。之后的部分建议写一些可能很难识别的专用名词。此外，每一句话的前一句也会通过该脚本添加到prompt中。因此，这里的prompt长度建议不超过120个单词。
    # whisper_prompt: str = "Hello, welcome to my lecture. Game dev about splines, bezier curve, De Casteljau's algorithm jerk."
    # whisper_prompt: str = 'こんにちは、私の講義へようこそ。'
    whisper_prompt: str = 'Hello, welcome to my lecture. And this is a video about Godot game dev. Slay The Spire, bat, crab, bats, setter, getter, .tscn, packed scene, .gd, .res'
    # 用逗号断句的句子长度阈值
    comma_as_end_threshold: int = 80
    # 调用翻译api每次发送的字符上限, 建议英文4500，日文1600。否则可能会报API server error.
    api_character_limit = 4200
    # 任务类型 transcribe | translate
    task: str = 'transcribe'
    # 翻译后只保留中文字幕
    only_zh: bool = False
    # 使用百度api
    use_baidu_api: bool = False
    # 使用chatglm-6b进行翻译。 速度慢，效果也差。
    # use_chatglm: bool = False
    baidu_appid: str = ''
    baidu_appkey: str = ''
    # 翻译源语言
    src_lang: str = 'en'
    # 翻译目标语言
    tgt_lang: str = 'zh'
