#!/bin/bash

# Upload the most recent file to an SFTP server from a local directory, and create a backup.
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
# The script also checks the local directory for files that match the naming convention 
# stablished by "FILE_NAME_PREFIX" variable. For example, we have the file name:
#           ACCESS-LOG-APACHE_YYYYMMDD_HHMMSS.txt
# We would stablish the prefix as:
#           FILE_NAME_PREFIX="ACCESS-LOG-APACHE_"
#
# The script will copy the uploaded file to a backup directory.

# Variables
SERVER_NAME='' # Hostname as defined in ~/.ssh/config, e.g., sftp-prod
PATH_UPLOAD_DEST='' # Destination directory where the file will be uploaded to the SFTP server
PATH_UPLOAD_BACK='' # Backup directory where the file will be saved before uploading to the destination
PATH_UPLOAD_SOURCE='' # Directory on the local machine where the files are located, e.g., /var/log/apache/
FILE_NAME_PREFIX='' # Prefix of the file to upload, e.g., "ACCESS-LOG-APACHE_"
LS_TEMP_FILE='/tmp/sftp_upload_check.txt' # Temporary file to store the list of files from the SFTP server, 
                                          # used for checking if the file was uploaded successfully to SFTP server, 
                                          # will be deleted after the script runs
LOGFILE='' # Log file to record the script's actions

# Function: write message to log file
log_message() {
    local now
    now=$(date "+%d-%m-%Y %H:%M:%S")
    echo "[$now] $1" >> "$LOGFILE"
}

# Function: check that directory exists
validate_directory() {
    if [ ! -d "$1" ]; then
        log_message "Directory $1 does not exist."
        exit 1
    fi
}

# Function: find most recent file matching prefix
find_file_to_upload() {
    local file
    file=$(ls -1t "$PATH_UPLOAD_SOURCE" 2>/dev/null | grep "^$FILE_NAME_PREFIX" | head -n 1)
    if [ -z "$file" ]; then
        log_message "No file found with prefix $FILE_NAME_PREFIX in $PATH_UPLOAD_SOURCE."
        exit 1
    fi
    echo "$file"
}

# Function: upload file to remote SFTP server
upload_file() {
    local file=$1
    log_message "Uploading file $file to SFTP server $SERVER_NAME into $PATH_UPLOAD_DEST..."
    sftp "$SERVER_NAME" <<EOF
cd $PATH_UPLOAD_DEST
put $PATH_UPLOAD_SOURCE/$file
bye
EOF

    if [ $? -ne 0 ]; then
        log_message "Error uploading file $file to SFTP server $SERVER_NAME."
        exit 1
    fi
}

# Function: verify that file was uploaded
verify_upload() {
    local file=$1
    log_message "Verifying that file $file was uploaded correctly to SFTP server $SERVER_NAME..."
    sftp "$SERVER_NAME" <<EOF > "$LS_TEMP_FILE"
cd $PATH_UPLOAD_DEST
ls -1t
bye
EOF

    if [ $? -ne 0 ]; then
        log_message "Error listing remote directory on SFTP server $SERVER_NAME for verification."
        rm -f "$LS_TEMP_FILE"
        exit 1
    fi

    local upload_success
    upload_success=$(grep -w "^$file\$" "$LS_TEMP_FILE")
    if [ -z "$upload_success" ]; then
        log_message "File $file was not found on SFTP server $SERVER_NAME after upload."
        rm -f "$LS_TEMP_FILE"
        exit 1
    else
        log_message "File $file was uploaded successfully to SFTP server $SERVER_NAME."
    fi

    rm -f "$LS_TEMP_FILE"
}

# Function: save a backup copy of uploaded file
backup_file() {
    local file=$1
    log_message "Saving backup copy of file $file into $PATH_UPLOAD_BACK..."
    cp -f "$PATH_UPLOAD_SOURCE/$file" "$PATH_UPLOAD_BACK/"

    if [ $? -ne 0 ]; then
        log_message "Error saving backup copy of file $file."
        exit 1
    fi
}

# Function: delete the source file after upload
delete_source_file() {
    local file=$1
    log_message "Deleting source file $file from $PATH_UPLOAD_SOURCE..."
    rm -f "$PATH_UPLOAD_SOURCE/$file"

    if [ $? -ne 0 ]; then
        log_message "Error deleting source file $file from $PATH_UPLOAD_SOURCE."
        exit 1
    fi
}

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

log_message "#################################"
log_message "# Start of upload process"
log_message "#################################"

# Validate required directories exist
validate_directory "$PATH_UPLOAD_SOURCE"
validate_directory "$PATH_UPLOAD_BACK"

# Find most recent file matching prefix
FILE_TO_UPLOAD=$(find_file_to_upload)
if [ -z "$FILE_TO_UPLOAD" ]; then
    log_message "No file found with prefix $FILE_NAME_PREFIX. Exiting script."
    log_message "#################################"
    exit 1
fi
log_message "File to upload: $FILE_TO_UPLOAD"

# Upload file
upload_file "$FILE_TO_UPLOAD"
if [ $? -ne 0 ]; then
    log_message "Could not upload file $FILE_TO_UPLOAD. Exiting script."
    log_message "#################################"
    exit 1
fi

# Verify upload
verify_upload "$FILE_TO_UPLOAD"
if [ $? -ne 0 ]; then
    log_message "Could not verify upload of file $FILE_TO_UPLOAD. Exiting script."
    log_message "#################################"
    exit 1
fi

# Backup file locally
backup_file "$FILE_TO_UPLOAD"

# Delete source file
delete_source_file "$FILE_TO_UPLOAD"

log_message "Upload process completed successfully."
log_message "#################################"
exit 0
