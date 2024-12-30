from pushover import Pushover


class Push(object):

    def __init__(self, user_key, api_token):
        self.client = Pushover(token=api_token)
        self.client.user(user_token=user_key)

    def send_message(self, message, title=None):
        msg = self.client.msg(message)
        if title:
            msg.set("title", title)
        self.client.send(msg)
