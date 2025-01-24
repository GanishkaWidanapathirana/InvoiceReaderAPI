import os


def save_file(uploaded_file, destination_folder="data/uploads/"):
    """
    Save an uploaded file to a specified directory.
    """
    os.makedirs(destination_folder, exist_ok=True)
    file_path = os.path.join(destination_folder, uploaded_file.filename)

    with open(file_path, "wb") as buffer:
        buffer.write(uploaded_file.file.read())
    return file_path
