from django import template
import re
register = template.Library()

@register.filter('youtubize')
def youtubize(value):
    """
    Converts http:// links to youtube into youtube-embed statements, so that
    one can provide a simple link to a youtube video and this filter will
    embed it.
    
    Based on the Django urlize filter.
    """
    text = value
    # Configuration for urlize() function
    LEADING_PUNCTUATION  = ['(', '<', '&lt;']
    TRAILING_PUNCTUATION = ['.', ',', ')', '>', '\n', '&gt;']
    word_split_re = re.compile(r'(\s+)')
    punctuation_re = re.compile('^(?P<lead>(?:%s)*)(?P<middle>.*?)(?P<trail>(?:%s)*)$' % \
            ('|'.join([re.escape(x) for x in LEADING_PUNCTUATION]),
            '|'.join([re.escape(x) for x in TRAILING_PUNCTUATION])))
    youtube_re = re.compile ('http://www.youtube.com/watch.v=(?P<videoid>(.+))')
    
    
    words = word_split_re.split(text)
    for i, word in enumerate(words):
        match = punctuation_re.match(word)
        if match:
            lead, middle, trail = match.groups()
            if middle.startswith('http://www.youtube.com/watch') or middle.startswith('http://youtube.com/watch'):
                video_match = youtube_re.match(middle)
                if video_match:
                    video_id = video_match.groups()[1]
                    middle = '''<br><object width="170" height="140">
      <param name="movie" value="http://www.youtube.com/v/%s"/>
      <param name="wmode" value="transparent"/>
      <embed src="http://www.youtube.com/v/%s" type="application/x-shockwave-flash" wmode="transparent" width="170" height="170"/>
    </object><br>''' % (video_id, video_id)

            if lead + middle + trail != word:
                words[i] = lead + middle + trail
    return ''.join(words)