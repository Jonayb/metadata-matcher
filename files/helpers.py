import os
from datetime import datetime
import piexif
from fractions import Fraction


def search_media(path, title, media_moved, non_edited_dir, edited_word):
    """
    Searches for media associated with the JSON file.

    Args:
        path: Directory path where media files are stored.
        title: Original media title from the JSON file.
        media_moved: List of already moved media titles to avoid duplicates.
        non_edited_dir: Directory where non-edited media will be moved.
        edited_word: Word used to identify edited versions of files.

    Returns:
        The real title of the matched media if found, otherwise None.
    """
    title = sanitize_title(title)

    # Attempt to find the media file using the edited title format.
    real_title = find_existing_media(path, title, suffix=edited_word)

    # If not found, attempt to find the media file using the original title format.
    if not real_title:
        real_title = find_existing_media(path, title, suffix='', is_edited=False)

    # If still not found, check for a duplicate name with a numbered suffix like (1), (2), etc.
    if not real_title:
        real_title = find_duplicate_name(title, media_moved, recursion_level=1)

    # If not found, attempt to truncate the title (to handle filesystem limits) and search again.
    if not real_title:
        short_title = truncate_title(title, length=47)  # Truncate the title to 47 characters.
        real_title = find_existing_media(path, short_title, suffix=edited_word)

        # If the truncated version isn't found, check for a duplicate name with the truncated title.
        if not real_title:
            real_title = find_duplicate_name(short_title, media_moved, recursion_level=1)

    # If a valid title is found, move the associated file to the non-edited directory.
    if real_title:
        move_to_non_edited(os.path.join(path, real_title), non_edited_dir)

    # Return the found title or None if no media file was found.
    return real_title


def find_existing_media(path, title, suffix, is_edited=True):
    """
    Finds media file by checking the existence of various possible filenames.

    Args:
        path: Directory path
        title: Original media title
        suffix: Suffix to add to the title (e.g., "-bewerkt")
        is_edited: Boolean to indicate if the file is edited

    Returns:
        The real title if found, None otherwise
    """
    possible_title = f"{title.rsplit('.', 1)[0]}{suffix}.{title.rsplit('.', 1)[1]}"
    possible_path = os.path.join(path, possible_title)

    if os.path.exists(possible_path):
        return possible_title

    if is_edited:
        possible_title = f"{title.rsplit('.', 1)[0]}(1).{title.rsplit('.', 1)[1]}"
        possible_path = os.path.join(path, possible_title)

        if os.path.exists(possible_path) and not os.path.exists(os.path.join(path, f"{title}(1).json")):
            return possible_title

    return None


def truncate_title(title, length=47):
    """Truncates the title to a specified length."""
    return f"{title.rsplit('.', 1)[0][:length]}.{title.rsplit('.', 1)[1]}"


def move_to_non_edited(filepath, destination_dir):
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


def find_duplicate_name(title, media_moved, recursion_level=1):
    """
    Recursively searches for a non-duplicate name by appending a number.

    Args:
        title: Original title
        media_moved: List of already moved media titles
        recursion_level: Current recursion level (appended to the title)

    Returns:
        Non-duplicate title
    """
    title_candidate = f"{title.rsplit('.', 1)[0]}({recursion_level}).{title.rsplit('.', 1)[1]}"

    if title_candidate in media_moved:
        return find_duplicate_name(title, media_moved, recursion_level + 1)

    return title_candidate


def create_folders(matched_dir, non_edited_dir):
    """
    Creates the necessary folders if they don't exist.

    Args:
        matched_dir: Directory for matched media
        non_edited_dir: Directory for non-edited (original) media
    """
    os.makedirs(matched_dir, exist_ok=True)
    os.makedirs(non_edited_dir, exist_ok=True)


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
        filepath: Path to the image file
        image: PIL image object
        lat: Latitude
        lng: Longitude
        altitude: Altitude
        timestamp: Timestamp to set as EXIF DateTime
    """
    exif_dict = piexif.load(image.info.get('exif', b''))

    date_time = datetime.utcfromtimestamp(int(timestamp)).strftime('%Y:%m:%d %H:%M:%S')
    exif_dict['0th'][piexif.ImageIFD.DateTime] = date_time
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
