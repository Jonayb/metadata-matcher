# Metadata Matcher for Google Photos

Welcome to the improved and actively maintained fork of [GooglePhotosMatcher](https://github.com/anderbggo/GooglePhotosMatcher/tree/main). This version is faster, cleaner, and fixes critical bugs that affected your photo metadata.

### What's New:
- **Preserve Original Metadata**: Fixed issues where original photo metadata was lost.
- **Keep Original File Sizes**: Fixed the issue where file sizes varied after processing.
- **Accurate Time Zones**:  Corrected timestamp processing. The UTC datetime from Google Takeout is now switched to the correct timezone from location latitude and longitude.

## Restore Your Photo Metadata in 3 Easy Steps:

1. **Download Your Photos**: Use [Google Takeout](https://takeout.google.com/) to get your media. Unzip the files.
2. **Run MetaMatcher**: Download and execute `MetaMatcher.exe`.
3. **Click Match**: Select your folder and let the tool do the rest. Matched files will be saved in a new `Matched` folder.

## Why Choose This Tool?
- **Effortless Metadata Recovery**: Automatically restores dates and locations to your photos and videos.
- **Handles Edited Files**: Keeps your original and edited versions organized.
- **Compatible with Any JSON**: Works beyond Google Photos—simply ensure your image and JSON share the same name, and the metadata will be matched.

## FAQs

### What’s in the _Originals_ Folder?
Edited photos/videos are saved in `Matched`, while originals are in `Originals`.

### Why Are Some Files Unmatched?
Special characters in filenames can cause mismatches. Some filetypes are also not supported. Currently, JPG, JPEG, TIF, and TIFF are supported.

## Contributors
- anderbggo - Original author
- Jonayb - Fork maintainer and lead developer of the improved version.
