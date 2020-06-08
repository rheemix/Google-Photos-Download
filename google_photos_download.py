import os
import time
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
from urllib.request import urlretrieve as download
from win32_setctime import setctime

# Define Scopes for Application

SCOPES = ['https://www.googleapis.com/auth/photoslibrary']


# Get Google Photos API Service
def get_service():
    # The file photos_token.pickle stores the user's access and refresh tokens,
    # and is created automatically when the authorization flow completes
    # for the first time.
    creds = None

    if os.path.exists('photoslibrary_token.pickle'):
        with open('photoslibrary_token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open('photoslibrary_token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('photoslibrary', 'v1', credentials=creds)


# Download all available images from Google Photos
def download_images(media_items):
    media_num = 0      # Total number of medial files
    download_num = 0   # Number of downloaded files
    skip_num = 0       # Number of skipped files - already downloaded
    error_num = 0      # Number of download errors
    new_download = ''  # Downloaded file list

    for x in media_items:
        filename = x['filename']
        fd = x['mediaMetadata']['creationTime']  # Read file picture taken date/time
        # Create datetime variable from metadata. Subtract 4 hours for timezone differences
        date = datetime(int(fd[0:4]), int(fd[5:7]), int(fd[8:10]), int(fd[11:13]),
                        int(fd[14:16]), int(fd[17:19])) - timedelta(hours=4)
        utime = time.mktime(date.timetuple())  # Create tuple time format to be used later
        file_name_date = filename + ' ' + str(date)

        # File is image type
        if 'image' in x['mimeType']:
            url = x['baseUrl'] + '=d'
            f_download_file = bool(1)

        # File is video type
        elif 'video' in x['mimeType']:
            video_status = x['mediaMetadata']['video']['status']
            # Allow download only if video file is in READY state
            # Other states cause download errors
            if 'READY' in video_status:
                url = x['baseUrl'] + '=dv'
                f_download_file = bool(1)
            else:
                print('*** ATTENTION: Video Status is not READY for ' + filename + ' ***')
                f_download_file = bool(0)

        # File not neither a image or a video
        else:
            f_download_file = bool(0)

        # Do not download
        if not f_download_file:
            print('*** ATTENTION: Not attempting to download ' + filename + ' ***')
            new_download = new_download + '\n\t*** Video not ready *** ' + filename
            error_num += 1

        # Download image/video file only if it has not been downloaded previously
        elif file_name_date not in file_list:  # Check if the file was NOT downloaded previously
            try:
                print('Downloading ' + filename)
                name, ext = os.path.splitext(filename)

                if os.path.exists(path + '\\' + filename):  # If same file exists, add utime to file name
                    filename = name + '_' + str(utime) + ext
                download(url, path + '\\' + filename)  # Download
            except:
                new_download = new_download + '\n\t*** Download Failed *** ' + filename
            else:
                new_download = new_download + '\n\tDownloaded ' + filename

                # Update file modified/accessed/created time to be the same as picture taken time
                os.utime(path + '\\' + filename, (utime, utime))
                setctime(path + '\\' + filename, utime)
                f.write(file_name_date + '\n')  # Add file name to list of downloaded files
                download_num += 1

            # Google Photos API does not have a way to identify if Live Photos are available
            # Try to download it and see if it works
            if 'image' in x['mimeType']:
                try:
                    filename = name + '.MOV'
                    print('Attempting to download live photo ' + filename)
                    if os.path.exists(path + '\\' + filename):  # If same file exists, add utime to file name
                        filename = name + '_' + str(utime) + '.MOV'
                    download(url + 'v', path + '\\' + filename)  # Try downloading live photo
                except:
                    # No live photos
                    print(' - No Live Photo for ' + filename)
                else:
                    print(' - Live Photo downloaded ' + filename)
                    # Update file modified/accessed/created time to be the same as picture taken time
                    os.utime(path + '\\' + filename, (utime, utime))
                    setctime(path + '\\' + filename, utime)
                    f.write(filename + ' ' + str(date) + '\n')  # Add file name to list of downloaded files
                    new_download = new_download + '\n\tDownloaded ' + filename
                    download_num += 1
                    media_num += 1
        # File was previously downloaded. Skip
        else:
            print('Skipping ' + filename + '. Already downloaded.')
            skip_num += 1

        media_num += 1
    return media_num, download_num, skip_num, error_num, new_download


# Initializations
total_media = 0
total_download = 0
total_skip = 0
total_error = 0

# Get API Service
# print('Getting API Service...')
service = get_service()
# print('API Service loaded.\n')

# Find and Download Media
path = 'Google Photos Library'
if not os.path.exists(path):
    os.makedirs(path)

if os.path.exists("download_list.txt"):
    f = open("download_list.txt", "r")
    file_list = f.read()    # Read list of downloaded files
else:
    file_list = ''

f = open("download_list.txt", "a+")  # Open file again to record file names as new files are downloaded

results = service.mediaItems().list(pageSize=100).execute()  # Get items from Google Photos
media_num, download_num, skip_num, error_num, new_download = download_images(results['mediaItems'])  # Down files
total_media += media_num
total_download += download_num
total_skip += skip_num
total_error += error_num
next = results['nextPageToken']

# Google Photos API only allows up to 100 images to be processed at once
# Keep trying to process next batch until there's no more
while True:
    results = service.mediaItems().list(pageSize=100, pageToken=next).execute()  # Get items from Google Photos
    if len(results) == 1:
        break
    media_num, download_num, skip_num, error_num, new_download = download_images(results['mediaItems'])  # Down files
    total_media += media_num
    total_download += download_num
    total_skip += skip_num
    total_error += error_num
    try:
        next = results['nextPageToken']
    except KeyError:
        break

print('\n************************')
print(' Total Files      = ' + str(total_media))
print(' Downloaded Files = ' + str(total_download))
print(' Skipped Files    = ' + str(total_skip))
print(' Error Files      = ' + str(total_error))
print('************************')

input("\nPress Enter to continue...")
