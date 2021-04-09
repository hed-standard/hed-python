import json
import os.path
from hed.web.web_utils import generate_filename, generate_download_file_response, \
    generate_text_response,get_hed_path_from_pull_down, \
    get_uploaded_file_path_from_form, save_text_to_upload_folder, get_optional_form_field


if __name__ == '__main__':
    response = generate_text_response("", msg='JSON dictionary had no validation errors')
    print(response)


