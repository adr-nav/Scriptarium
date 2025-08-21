#!/bin/bash

# Download the most recent file from an SFTP server, save it to a local directory, and create a backup.
#
# This script is intended to be run on a Linux server and is designed to log in to an SFTP server using
# the SSH key found in the configuration file located at ~/.ssh/config.
#
# The ~/.ssh/config file must contain the necessary configuration to connect to the SFTP server, for example:
#   Host sftp-prod
#       HostName sftp-prod.contoso.com
#       User contosoUser
#       IdentityFile ~/.ssh/id_rsa_contoso
#       Port 22
#          
# The script also checks the SFTP server for files that match the naming convention 
# stablished by "FILE_NAME_PREFIX" variable. For example, we have the file name:
#           ACCESS-LOG-APACHE_YYYYMMDD_HHMMSS.txt
# We would stablish the prefix as:
#           FILE_NAME_PREFIX="ACCESS-LOG-APACHE_"
#
# The script will copy the downloaded file to a backup directory and a destination directory.

# Variables, to avoid error messages, please fill in the following variables before running the script:
SERVER_NAME='' # Hostname as defined in ~/.ssh/config, e.g., sftp-prod
PATH_DOWNLOAD_DEST='' # Destination directory where the file will be copied
PATH_DOWNLOAD_BACK='' # Backup directory where the file will be saved before copying to the destination
PATH_DOWNLOAD_SOURCE='' # Directory on the SFTP server where the files are located, e.g., /upload
LS_TEMP_FILE='/tmp/sftp_file_list.txt' # Temporary file to store the list of files from the SFTP server, will be deleted after the script runs
FILE_NAME_PREFIX="" # Prefix of the file to download, e.g., "ACCESS-LOG-APACHE_"
FILE_NAME_EXTENSION="" # File extension to search for WITH NO dot on it, e.g., "txt" and not ".txt"
LOGFILE='' # Log file to record the script's actions
TIMESTAMP=`date "+%d-%m-%Y %H:%M:%S"` # Feel free to change the date format as needed, this is the format used in the log file

# Function to log messages to a log file 
log_message() {
    echo "[$TIMESTAMP] $1" >> $LOGFILE
}

# function to validate that a directory exists
validate_directory() {
    if [ ! -d "$1" ]; then
        log_message "Folder $1 does not exist."
        exit 1
    fi
}

# Function to connect to the SFTP server and list files. DO NOT indent the here-document (EOF) to avoid issues with the SFTP command.
list_files_on_sftp() {
    log_message "Connecting to server $SERVER_NAME to get a list of files..."
    sftp $SERVER_NAME <<EOF > $LS_TEMP_FILE
cd $PATH_DOWNLOAD_SOURCE
ls -1
bye
EOF

    if [ $? -ne 0 ]; then
        log_message "Error getting a list of files from SFTP server: $SERVER_NAME"
        exit 1
    fi
}

# Function to search for the most recent file that matches the FILE_NAME_PREFIX
find_file_to_download() {
    local file=$(grep -E "^$FILE_NAME_PREFIX.*\.$FILE_NAME_EXTENSION$" $LS_TEMP_FILE | tail -n 1)
    if [ -z "$file" ]; then
        log_message "No file found with preffix: $FILE_NAME_PREFIX and extension: $FILE_NAME_EXTENSION in $LS_TEMP_FILE."
        exit 1
    fi
    echo "$file"
}

# Function to download the file from the SFTP server
download_file() {
    local file=$1
    log_message "Downloading $file in backup folder $PATH_DOWNLOAD_BACK..."
    sftp $SERVER_NAME <<EOF
cd $PATH_DOWNLOAD_SOURCE
get $file $PATH_DOWNLOAD_BACK/$file
bye
EOF

    if [ $? -ne 0 ]; then
        log_message "Error downloading $file from SFTP server $SERVER_NAME."
        exit 1
    fi

    # Copy the downloaded file from backup folder to the destination folder
    log_message "Copying file $file to destination folder $PATH_DOWNLOAD_DEST..."
    cp $PATH_DOWNLOAD_BACK/$file $PATH_DOWNLOAD_DEST/$file
    if [ $? -ne 0 ]; then
        log_message "Error copying file $file to destination folder $PATH_DOWNLOAD_DEST."
        exit 1
    fi

}

# Function to verify that the file was downloaded correctly and exists in both the destination and backup directories
verify_download() {
    local file=$1
    local dest_check=0
    local back_check=0

    if [ -f "$PATH_DOWNLOAD_DEST/$file" ]; then
        log_message "File successfully downloaded to destination folder: $PATH_DOWNLOAD_DEST/$file."
    else
        log_message "File $file not found in destination folder: $PATH_DOWNLOAD_DEST."
        dest_check=1
    fi

    if [ -f "$PATH_DOWNLOAD_BACK/$file" ]; then
        log_message "File successfully downloaded to backup folder $PATH_DOWNLOAD_BACK/$file."
    else
        log_message "File $file not found in backup folder: $PATH_DOWNLOAD_BACK."
        back_check=1
    fi

    if [ $dest_check -ne 0 ] || [ $back_check -ne 0 ]; then
        log_message "There has been an issue downloading the file. Please check the logs."
        exit 1
    fi
}

# Script starts here
log_message "#################################"
log_message "# Starting file download script #"
log_message "#################################"

# Validate that the folders exist
validate_directory "$PATH_DOWNLOAD_DEST"
log_message "Destination folder $PATH_DOWNLOAD_DEST exists."

validate_directory "$PATH_DOWNLOAD_BACK"
log_message "Backup folder $PATH_DOWNLOAD_BACK exists."

# List files on the SFTP server
list_files_on_sftp

# Search for the most recent file that matches the prefix and extension
FILE_TO_DOWNLOAD=$(find_file_to_download)

if [ -z "$FILE_TO_DOWNLOAD" ]; then
    log_message "No file found to be downloaded."
    log_message "#################################"
    exit 1
fi

log_message "File found: $FILE_TO_DOWNLOAD"

# Download the file from the SFTP server
download_file "$FILE_TO_DOWNLOAD"

# Verify that the file was downloaded correctly
verify_download "$FILE_TO_DOWNLOAD"

log_message "Download completed successfully."
log_message "#################################"
exit 0