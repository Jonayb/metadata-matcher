import os
import json
from PIL import Image
from helpers import create_folders, search_media, set_exif


def main_process(browser_path, window, edited_word):
    piexif_codecs = {'tif', 'tiff', 'jpeg', 'jpg'}
    media_moved = []  # List of already matched media
    matched_media_path = os.path.join(browser_path, "Matched")
    original_media_path = os.path.join(browser_path, "Originals")
    edited_word = edited_word or '-editado'
    error_counter = 0
    success_counter = 0

    try:
        # Convert iterator to a list and sort by length to process shorter names first
        files = sorted(os.scandir(browser_path), key=lambda s: len(s.name))
        create_folders(matched_media_path, original_media_path)
    except Exception as e:
        window['-PROGRESS_LABEL-'].update("Choose a valid directory", visible=True, text_color='red')
        return

    total_files = len(files)

    for index, entry in enumerate(files):
        if entry.is_file() and entry.name.endswith(".json"):
            try:
                with open(entry.path, encoding="utf8") as f:
                    data = json.load(f)
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON {entry.name}: {e}")
                error_counter += 1
                continue

            progress = round((index + 1) / total_files * 100, 2)
            window['-PROGRESS_LABEL-'].update(f"{progress}%", visible=True)
            window['-PROGRESS_BAR-'].update(progress, visible=True)

            # Search for associated media
            title_original = data.get('title', '')

            try:
                title = search_media(browser_path, title_original, media_moved, original_media_path, edited_word)
            except Exception as e:
                print(f"Error in search_media() with file {title_original}: {e}")
                error_counter += 1
                continue

            if title is None or title == 'None':
                print(f"{title_original} not found")
                error_counter += 1
                continue

            filepath = os.path.join(browser_path, title)
            timestamp = int(data['photoTakenTime']['timestamp'])
            print(filepath)

            file_extension = title.rsplit('.', 1)[-1].casefold()
            if file_extension in piexif_codecs:
                try:
                    with Image.open(filepath) as im:
                        set_exif(
                            filepath=filepath,
                            image=im,
                            lat=data['geoData']['latitude'],
                            lng=data['geoData']['longitude'],
                            altitude=data['geoData']['altitude'],
                            timestamp=timestamp
                        )
                except Exception as e:
                    print(f"Error handling EXIF data for {title}: {e}")
                    error_counter += 1
                    continue

            # Move file and delete JSON
            try:
                os.replace(filepath, os.path.join(matched_media_path, title))
                os.remove(entry.path)
            except OSError as e:
                print(f"Error moving or deleting file {title}: {e}")
                error_counter += 1
                continue

            media_moved.append(title)
            success_counter += 1

    success_message = " success" if success_counter == 1 else " successes"
    error_message = " error" if error_counter == 1 else " errors"

    # Update the interface
    window['-PROGRESS_BAR-'].update(100, visible=True)
    window['-PROGRESS_LABEL-'].update(
        f"Matching process finished with {success_counter}{success_message} and {error_counter}{error_message}.",
        visible=True
    )
