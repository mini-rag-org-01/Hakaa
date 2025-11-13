from .BaseControler import BaseControler
from fastapi import  UploadFile
from models import ResponseSignal
class DataControler(BaseControler):
    def __init__(self):
        super().__init__()
        self.size_scale = 1048576 # convert MB to Bytes

    def validate_uploaded_file(self, file: UploadFile):

        if file.content_type not in self.app_settings.FILE_ALLOWED_TYPES:
            return False, ResponseSignal.FILE_TYPE_NOT_SUPPORTED
        
        if file.size > self.app_settings.FILE_MAX_SIZE * self.size_scale:
            return False, ResponseSignal.FILE_SIZE_EXCEEDED
        
        return True ,ResponseSignal.FILE_UPLOADED_SUCCESS
    
    def generate_unique_filename(self, )