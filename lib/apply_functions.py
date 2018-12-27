
def get_text(soup):
    return soup.text


def get_url(soup):
    return soup['href']


def strip(text, chars):
    return text.strip(chars)


def get_image_url(soup):
    return soup['loadlate']
