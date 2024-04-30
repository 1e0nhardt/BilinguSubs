from pytube import YouTube, Playlist, StreamQuery
import subprocess
import os
import requests
from utils import LOGGER, ensure_folder_exists
from dataclasses import dataclass
import tyro


@dataclass
class DownloadConfig:
    dest_dir: str = 'assets/video/'
    download_dir: str = 'assets/audio/'
    misc_dir: str = 'assets/misc/'
    # YouTube URL.
    url: str = 'https://www.youtube.com/watch?v=EYt6uDr-PHQ'
    # 下载播放列表时给文件名加的前缀
    prefix: str = ''


class YoutubeDownloader(object):
    
    def __init__(self, config: DownloadConfig) -> None:
        self.config = config
        self.playlist_urls = []
    

    def run(self):
        if self.config.url.find('list') == -1:
            self.download_video()
        else:
            self.download_video_list()


    # 下载封面
    def download_thumbnail(self, url, filename):
        # 发送 GET 请求并获取响应
        response = requests.get(url)
        # filename += os.path.splitext(url)[1]
        filename += '.jpg'
        # 处理特殊符号
        filename = filename.replace('<', '').replace('>', '').replace('\"', '').replace('/', '').replace('\\', '').replace('?', '').replace('*', '').replace('|', '-')
        # 保存图片到本地文件
        with open(self.config.misc_dir + filename, 'wb') as file:
            file.write(response.content)
        LOGGER.info(self.config.misc_dir + filename)


    # 下载单个视频
    def download_video(self):
        yt = YouTube(self.config.url, self.progress_callback, self.completed_callback)
        self.download_thumbnail(yt.thumbnail_url, yt.title)
        self.download_video_from_streams(yt.streams, yt.title)


    # 下载视频列表中的所有视频
    def download_video_list(self):
        play_list = Playlist(self.config.url)
        for i, video in enumerate(play_list.videos):
            self.playlist_urls.append(f'{i:03d} {video.watch_url}' + "\n")
            title = video.title
            prefix=self.config.prefix + f'{i:03d}' + '-'
            filename = prefix + title

            self.download_thumbnail(video.thumbnail_url, filename)

            video.register_on_progress_callback(self.progress_callback)
            video.register_on_complete_callback(self.completed_callback)
            self.download_video_from_streams(video.streams, filename)
        
        with open(self.config.misc_dir + 'urls.txt', 'w') as f:
            f.writelines(self.playlist_urls)
        LOGGER.info('urls write done!')


    # 选择视频质量(1080p)
    def download_video_from_streams(self, streams: StreamQuery, filename):
        video_stream = streams.filter(adaptive=True, mime_type="video/mp4").order_by('resolution').desc().first()
        audio_stream = streams.filter(mime_type="audio/mp4").order_by('abr').desc().first()
        
        filename += video_stream.resolution
        video_path = self.config.download_dir + filename + '.mp4'
        audio_path = self.config.download_dir + filename + '.m4a'
        output_path = self.config.dest_dir + filename + '.mp4'

        LOGGER.debug(video_path)
        LOGGER.debug(audio_path)
        LOGGER.debug(output_path)

        # 下载视频
        video_stream.download(filename=video_path)
        # 下载音频
        audio_stream.download(filename=audio_path)
        # 合并音视频
        subprocess.run(
            f"ffmpeg -i \"{video_path}\" -i \"{audio_path}\" -c:v copy -c:a copy \"{output_path}\""
        )
        # 移除纯视频
        os.remove(video_path)


    def progress_callback(self, info, data, remain_bytes):
        LOGGER.info(f'{info} Remain: {(remain_bytes / 1024**2):.2f}Mb')


    def completed_callback(self, info, path):
        LOGGER.info(f'{info}\n{path} downloaded!')


if __name__ == '__main__':
    args = tyro.cli(DownloadConfig)

    ensure_folder_exists(args.dest_dir)
    ensure_folder_exists(args.download_dir)
    ensure_folder_exists(args.misc_dir)

    downloader = YoutubeDownloader(args)
    downloader.run()
