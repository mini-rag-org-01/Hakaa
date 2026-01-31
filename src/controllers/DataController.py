from .BaseController import BaseController
from fastapi import  UploadFile
from models import ResponseSignal
from .ProjectController import ProjectController
import re
import os
class DataController(BaseController):
    def __init__(self):
        super().__init__()
        self.size_scale = 1048576 # convert MB to Bytes

    def validate_uploaded_file(self, file: UploadFile):

        if file.content_type not in self.app_settings.FILE_ALLOWED_TYPES:
            return False, ResponseSignal.FILE_TYPE_NOT_SUPPORTED
        
        if file.size > self.app_settings.FILE_MAX_SIZE * self.size_scale:
            return False, ResponseSignal.FILE_SIZE_EXCEEDED
        
        return True ,ResponseSignal.FILE_UPLOADED_SUCCESS
    
    def generate_unique_filepath(self, orig_file_name: str, project_id: str):
        # Generate a random string to guarantee the filename is unique
        random_key = self.generate_random_string()

        # Get the directory path where this specific project's files will be stored
        project_path = ProjectController().get_project_path(project_id=project_id)

        # Clean the original filename (remove spaces, special characters, etc.)
        cleaned_file_name = self.get_clean_file_name(
            orig_file_name=orig_file_name
        )

        # Join the project directory path with the generated unique filename
        # Final filename format: <randomString>_<cleanedFileName>
        new_file_path = os.path.join(
            project_path,
            random_key + "_" + cleaned_file_name
        )

        while os.path.exists(new_file_path):
                    random_key = self.generate_random_string()
                    new_file_path = os.path.join(
                        project_path,
                        random_key + "_" + cleaned_file_name
                    )

        return new_file_path, random_key + "_" + cleaned_file_name


    def get_clean_file_name(self, orig_file_name: str):
        # remove any special characters, except underscore and .
        cleaned_file_name = re.sub(r'[^\w.]', '', orig_file_name.strip())

        # replace spaces with underscore
        cleaned_file_name = cleaned_file_name.replace(" ", "_")

        # return the cleaned version of the filename
        return cleaned_file_name
