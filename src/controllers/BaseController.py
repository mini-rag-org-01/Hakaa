from helpers.config import get_settings, Settings
import os
import random
import string

class BaseController:
    def __init__(self):
        self.app_settings = get_settings()
        self.base_dir = os.path.dirname(os.path.dirname(__file__))
        self.files_dir = os.path.join(
            self.base_dir,
            "assets/files"     )
        self.databases_dir = os.path.join(
            self.base_dir,
            "assets/databases"
        )
        # gemerate random string with size 12
    def generate_random_string(self, length: int=12):
            return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

    def get_database_path(self, db_name: str):
        if not os.path.exists(self.databases_dir):
            os.makedirs(self.databases_dir)

        return os.path.join(self.databases_dir, db_name)
