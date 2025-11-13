from helpers.config import get_settings, Settings

class BaseControler:
    def __init__(self):
        self.app_settings = get_settings()