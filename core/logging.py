import logging
import re


TRACKING_PATH = re.compile(r'(/orders/track/)[^/\s?]+')


class RedactOrderTokens(logging.Filter):
    def filter(self, record):
        record.msg = TRACKING_PATH.sub(r'\1[redacted]', record.getMessage())
        record.args = ()
        return True
