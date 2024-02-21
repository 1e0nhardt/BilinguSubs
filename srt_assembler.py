"""
result
{
  'text': 全文本,
  'segments': [seg_dict, ....],
  'language': 语言
}

seg_dict
{
  'id': 序号,
  'seek': ?,
  'start': 片段开始时间,
  'end': 片段结束时间,
  'text': 片段文本,
  'tokens', 'temperature', 'avg_logprob', 'compression_ratio', 'no_speech_prob', : 模型参数和输出,
  'words': 需要设置word_timestamps=True。[{word: 单词, start: 单词开始时间, end: 单词结束时间, probability: 准确率}],
}
"""

class SrtAssembler(object):
    """从whisper结果生成srt文件
    
    comma_as_end_threshold: 如果句子中的逗号前已经有comma_as_end_threshold个字符，则直接在这里断句

    """
    def __init__(self, comma_as_end_threshold=90):
        self.srt_lines = []
        self.id = 0
        self.line_text = ''
        self.line_start = ''
        self.comma_as_end_threshold = comma_as_end_threshold
    
    def check_sentence_should_end(self, word):
        cond_a = word[-1] in '.?!。！？'
        cond_b = word[-1] in ',:;，；：、' and len(self.line_text) > self.comma_as_end_threshold
        return cond_a or cond_b
     
    def get_next_input(self, word_dict, offset=0.):
        word = word_dict['word']
        start = word_dict['start'] + offset
        end = word_dict['end'] + offset

        if self.line_text == '':
            self.id += 1
            self.line_start = start

        self.line_text += word

        if self.check_sentence_should_end(word):
            self.srt_lines.append({
                'id': self.id,
                'start': self.line_start,
                'end': end,
                'text': self.line_text
            })
            self.line_text = ''
    
    def get_clip_end_info(self, sr=16000):
        return (int(self.srt_lines[-1]['end'] * sr), self.srt_lines[-1]['text'])

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

    def generate_srt(self, filepath):
        srt_text = ''
        for line in self.srt_lines:
            srt_text += str(line['id']) + '\n'
            srt_text += self.get_timeline(line['start']) + ' --> ' + self.get_timeline(line['end']) + '\n'
            srt_text += line['text'].strip() + '\n'
            srt_text += '\n'

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(srt_text)

