import os
from datetime import datetime
import piexif
from fractions import Fraction
from timezonefinder import TimezoneFinder
import pytz

tf = TimezoneFinder()


def search_media(path, title, media_moved, original_dir, edited_word, truncated=False):
    """
    Searches for media associated with the JSON file.

    Args:
        path: Directory path where media files are stored.
        title: Original media title from the JSON file.
        media_moved: List of already moved media titles to avoid duplicates.
        original_dir: Directory where original media will be moved.
        edited_word: Word used to identify edited versions of files.
        truncated: Whether to truncate the media file's basename

    Returns:
        The real title of the matched media if found, otherwise None.
    """
    title = sanitize_title(title)
    if truncated:
        title = truncate_title(title)
    base_filename = title.rsplit('.', 1)[0]
    file_extension = title.rsplit('.', 1)[1]

    # Attempt to find the media file using the edited title format
    real_title = find_existing_media(path, base_filename, file_extension, suffix=edited_word, is_edited=True)

    if real_title:
        # If we have found the real (edited) title, move the normal title to the original folder
        move_to_original(os.path.join(path, title), original_dir)
        return real_title
    else:
        # Otherwise, attempt to find the media file using the original title format
        real_title = find_existing_media(path, base_filename, file_extension, suffix='', is_edited=False)

    if real_title:
        return real_title
    else:
        # Check for a duplicate name with a numbered suffix like (1), (2), etc.
        real_title = find_duplicate_name(path, base_filename, file_extension, media_moved, recursion_level=1)

    if real_title:
        return real_title
    elif not truncated:
        # Attempt the search again with the truncated title.
        return search_media(path, title, media_moved, original_dir, edited_word, truncated=True)

    return None  # Return None if no media file was found after all attempts.


def find_existing_media(path, base_filename, file_extension, suffix, is_edited=True):
    """
    Finds media file by checking the existence of various possible filenames.

    Args:
        path: Directory path
        base_filename: Original media title without extension
        file_extension: Extension of the media file
        suffix: Suffix to add to the title (e.g., "-bewerkt")
        is_edited: Boolean to indicate if the file is edited

    Returns:
        The real title if found, None otherwise
    """
    possible_title = f"{base_filename}{suffix}.{file_extension}"
    possible_path = os.path.join(path, possible_title)

    if os.path.exists(possible_path):
        return possible_title

    if is_edited:
        possible_title = f"{base_filename}(1).{file_extension}"
        possible_path = os.path.join(path, possible_title)

        if os.path.exists(possible_path) and not os.path.exists(os.path.join(path, f"{'.'.join((base_filename, file_extension))}(1).json")):
            return possible_title

    return None


def truncate_title(title, length=47):
    """Truncates the title to a specified length."""
    return f"{title.rsplit('.', 1)[0][:length]}.{title.rsplit('.', 1)[1]}"


def move_to_original(filepath, destination_dir):
    """Moves the original media to another folder."""
    os.replace(filepath, os.path.join(destination_dir, os.path.basename(filepath)))


def sanitize_title(title):
    """Removes incompatible characters from the title."""
    return (
        str(title)
        .replace("%", "")
        .replace("<", "")
        .replace(">", "")
        .replace("=", "")
        .replace(":", "")
        .replace("?", "")
        .replace("¿", "")
        .replace("*", "")
        .replace("#", "")
        .replace("&", "")
        .replace("{", "")
        .replace("}", "")
        .replace("\\", "")
        .replace("@", "")
        .replace("!", "")
        .replace("+", "")
        .replace("|", "")
        .replace("\"", "")
        .replace("\'", "")
    )


def find_duplicate_name(path, base_filename, file_extension, media_moved, recursion_level=1):
    """
    Recursively searches for a non-duplicate name by appending a number.

    Args:
        path: Directory path
        base_filename: Original title without extension
        file_extension: Extension of the original title
        media_moved: List of already moved media titles
        recursion_level: Current recursion level (appended to the title)

    Returns:
        Non-duplicate title if file exists, None otherwise
    """
    title_candidate = f"{base_filename}({recursion_level}).{file_extension}"
    possible_path = os.path.join(path, title_candidate)

    if title_candidate in media_moved or not os.path.exists(possible_path):
        if title_candidate in media_moved:
            return find_duplicate_name(path, base_filename, file_extension, media_moved, recursion_level + 1)
        else:
            return None

    return title_candidate


def create_folders(matched_dir, original_dir):
    """
    Creates the necessary folders if they don't exist.

    Args:
        matched_dir: Directory for matched media
        original_dir: Directory for original (non-edited) media
    """
    os.makedirs(matched_dir, exist_ok=True)
    os.makedirs(original_dir, exist_ok=True)


def to_deg(value, loc):
    """
    Convert decimal coordinates into degrees, minutes, and seconds tuple.

    Args:
        value: Decimal GPS value
        loc: Direction list ["S", "N"] or ["W", "E"]

    Returns:
        Tuple like (degrees, minutes, seconds, direction)
    """
    loc_value = loc[0] if value < 0 else loc[1]
    abs_value = abs(value)
    degrees = int(abs_value)
    minutes = int((abs_value - degrees) * 60)
    seconds = round((abs_value - degrees - minutes / 60) * 3600, 5)
    return degrees, minutes, seconds, loc_value


def change_to_rational(number):
    """
    Convert a number to a rational tuple.

    Args:
        number: Number to convert

    Returns:
        Tuple like (numerator, denominator)
    """
    frac = Fraction(str(number))
    return frac.numerator, frac.denominator


def set_exif(filepath, image, lat, lng, altitude, timestamp):
    """
    Sets EXIF data on an image file.

    Args:
        filepath: Path to the image file.
        image: PIL image object.
        lat: Latitude.
        lng: Longitude.
        altitude: Altitude.
        timestamp: UTC timestamp to set as EXIF DateTime.
    """
    exif_dict = piexif.load(image.info.get('exif', b''))

    # Determine the timezone based on latitude and longitude
    timezone_str = tf.timezone_at(lat=lat, lng=lng)

    if timezone_str:
        timezone = pytz.timezone(timezone_str)
        local_time = datetime.fromtimestamp(int(timestamp), timezone)
        date_time = local_time.strftime('%Y:%m:%d %H:%M:%S')
    else:
        # Fallback to UTC if timezone cannot be determined
        date_time = datetime.utcfromtimestamp(int(timestamp)).strftime('%Y:%m:%d %H:%M:%S')
        print("No location data, falling back to UTC.")

    exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal] = date_time
    exif_dict['Exif'][piexif.ExifIFD.DateTimeDigitized] = date_time

    try:
        lat_deg = to_deg(lat, ["S", "N"])
        lng_deg = to_deg(lng, ["W", "E"])

        gps_ifd = {
            piexif.GPSIFD.GPSVersionID: (2, 0, 0, 0),
            piexif.GPSIFD.GPSAltitudeRef: 1,
            piexif.GPSIFD.GPSAltitude: change_to_rational(round(altitude, 2)),
            piexif.GPSIFD.GPSLatitudeRef: lat_deg[3],
            piexif.GPSIFD.GPSLatitude: tuple(change_to_rational(x) for x in lat_deg[:3]),
            piexif.GPSIFD.GPSLongitudeRef: lng_deg[3],
            piexif.GPSIFD.GPSLongitude: tuple(change_to_rational(x) for x in lng_deg[:3]),
        }

        exif_dict['GPS'] = gps_ifd
    except Exception as e:
        print("Coordinates not set:", e)

    exif_bytes = piexif.dump(exif_dict)
    image.save(filepath, exif=exif_bytes)
