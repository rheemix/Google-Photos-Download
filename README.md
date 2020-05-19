# Google Photos Download
Download Google Photos

Written with Python 3 based on [GooglePhotosArchiver](https://github.com/NicholasDawson/GooglePhotosArchiver)
Instructions are also well documented in [GooglePhotosArchiver](https://github.com/NicholasDawson/GooglePhotosArchiver)

## Features
- Downloads all photos and videos to `Google Photos Library` directory
- Keeps track of downloaded files in `download_list.txt` file and subsequent downloads will skip previously downloaded files even if actual files are moved/deleted from `Google Photos Library` directory
- Correctly downloads live photos
  - Google Photos API currently does not provide a way to see if live photos exist or not
  - Code simply tries to download live photos for all photos and handles exceptions if fails to download
- Updates file creation date and modification date to be the same as picture taken date/time

## Required Libraries
- google-api-python-client
- google-auth-oauthlib
- google
- win32-setctime