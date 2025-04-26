import os

def get_upload_to(instance, filename, model_name, object_name, folder_type):
        return os.path.join(model_name ,object_name, folder_type, filename)