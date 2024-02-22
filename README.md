<a name="readme-top"></a>

[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]

简体中文 | [English](README_en.md)

<!-- ABOUT THE PROJECT -->
## 简介
基于OpenAI/Whisper的自动双语字幕生成。使用Whisper的word_timestamp特性实现智能断句并生成准确的时间轴。

<!-- GETTING STARTED -->
## 准备工作

### 在window上安装ffmpeg

1. 打开 https://www.gyan.dev/ffmpeg/builds/
2. 点击下载 ffmpeg-xxx-essentials.7z
3. 解压并将 ffmpeg-xxx-essentials_build/bin 添加到环境变量

### whisper环境
详见[whisper setup](https://github.com/openai/whisper?tab=readme-ov-file#setup)

### 安装

1. 将该库下载到本地
    ```sh
    git clone https://github.com/1e0nhardt/BilinguSubs.git
    ```
2. 安装需要的库
   ```sh
   pip install -r requirements.txt
   ```

<!-- USAGE EXAMPLES -->
## 使用方法

1. 将输入视频放到`assets/video/`文件夹下
2. 使用默认参数运行程序
    ```sh
    python app.py
    ```
3. 双语字幕会生成在`assets/video/`下。英文字幕和音频默认保存在`assets/srt/`和`assets/audio/`
4. 参数comma_as_end_threshold用于控制英文句子的长度，默认为80。
5. 使用`python app.py -h`获取更多信息

<!-- ACKNOWLEDGMENTS -->
## 效果展示

[示例1](25:51)(https://www.bilibili.com/video/BV15K42187te/)。
[示例2](1:56:32)(https://www.bilibili.com/video/BV1fJ4m1W7Sj/)。

<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/1e0nhardt/BilinguSubs.svg?style=for-the-badge
[contributors-url]: https://github.com/1e0nhardt/BilinguSubs/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/1e0nhardt/BilinguSubs.svg?style=for-the-badge
[forks-url]: https://github.com/1e0nhardt/BilinguSubs/network/members
[stars-shield]: https://img.shields.io/github/stars/1e0nhardt/BilinguSubs.svg?style=for-the-badge
[stars-url]: https://github.com/1e0nhardt/BilinguSubs/stargazers
[issues-shield]: https://img.shields.io/github/issues/1e0nhardt/BilinguSubs.svg?style=for-the-badge
[issues-url]: https://github.com/1e0nhardt/BilinguSubs/issues
[license-shield]: https://img.shields.io/github/license/1e0nhardt/BilinguSubs.svg?style=for-the-badge
[license-url]: https://github.com/1e0nhardt/BilinguSubs/blob/master/LICENSE.txt
