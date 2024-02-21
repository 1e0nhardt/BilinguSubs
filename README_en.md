<!-- Improved compatibility of back to top link: See: https://github.com/othneildrew/Best-README-Template/pull/73 -->
<a name="readme-top"></a>
<!--
*** Thanks for checking out the Best-README-Template. If you have a suggestion
*** that would make this better, please fork the repo and create a pull request
*** or simply open an issue with the tag "enhancement".
*** Don't forget to give the project a star!
*** Thanks again! Now go create something AMAZING! :D
-->



<!-- PROJECT SHIELDS -->
<!--
*** I'm using markdown "reference style" links for readability.
*** Reference links are enclosed in brackets [ ] instead of parentheses ( ).
*** See the bottom of this document for the declaration of the reference variables
*** for contributors-url, forks-url, etc. This is an optional, concise syntax you may use.
*** https://www.markdownguide.org/basic-syntax/#reference-style-links
-->
[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]

[简体中文](README.md) | English

<!-- ABOUT THE PROJECT -->
## About The Project

Automatic bilingual subtitle generation based on OpenAI/Whisper. Using Whisper's word timestamp feature to achieve intelligent sentence segmentation and generate an accurate timeline.


<!-- GETTING STARTED -->
## Setup

### Prerequisites
see [whisper setup](https://github.com/openai/whisper?tab=readme-ov-file#setup)

### Installation

1. Clone the repo
    ```sh
    git clone https://github.com/1e0nhardt/BilinguSubs.git
    ```
2. Install requirements
   ```sh
   pip install -r requirements.txt
   ```

<!-- USAGE EXAMPLES -->
## Usage

1. Place the input video in the `assets/video/` folder.
2. Run:
    ```sh
    python app.py
    ```
3. Bilingual subtitles will be generated in the `assets/video/` folder. English subtitles and audio are saved by default in `assets/srt/` and `assets/audio/` respectively.
4. The `comma_as_end_threshold` parameter controls the length of sentences and is set to 80 by default.
5. Use python app.py -h for more information.

<!-- ACKNOWLEDGMENTS -->
## Example

[check this video](https://www.bilibili.com/video/BV15K42187te/)


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
