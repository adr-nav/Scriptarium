#!/usr/bin/env python3

#
# Author: Adrián Navarro
# Email: contact@adrnav.com
# Last modified: 2025-08-22
#
# Script to send email alerts for Centreon host notifications
# using an external SMTP server (e.g., Office365).
# 
# The script constructs an HTML email with host details and sends it via SMTP.
# 
# Requirements:
# - Python 3
# - smtplib and email libraries (included in standard library)
# - argparse for command-line argument parsing
#
# Modify SMTP server settings, sender email, and password before use.
# 
# You will also need to create a new Notification Command in Centreon (Configuration > Commands > Notifications)
# with the following command line (adjust the path to this script):
# python3 $USER1$/notifications/centreon-host-email-notification.py --notify_type "$NOTIFICATIONTYPE$" --host_name "$HOSTNAME$" --host_alias "$HOSTALIAS$" --host_grpalias "$HOSTGROUPALIAS$" --host_state "$HOSTSTATE$" --host_address "$HOSTADDRESS$" --host_output "$HOSTOUTPUT$" --recipient_email "$CONTACTEMAIL$" --totalup "$TOTALHOSTSUP$" --totaldown "$TOTALHOSTSDOWN$" --duration "$HOSTDURATION$" --date "$DATE$" --time "$TIME$"
#
# Arguments explained:
# --notify_type: Type of notification (e.g., PROBLEM, RECOVERY)
# --host_name: Name of the host
# --host_alias: Alias of the host
# --host_grpalias: Alias of the host group (In my case I use it to automatically set the client name in my ticketing system)
# --host_state: Current state of the host (e.g., UP, DOWN)
# --host_address: IP address of the host
# --host_output: Additional information about the host state
# --recipient_email: Email address of the contact to notify
# --totalup: Total number of hosts that are UP
# --totaldown: Total number of hosts that are DOWN
# --duration: Duration of the current state
# --date: Date of the notification
# --time: Time of the notification
#
# Replace $USER1$ with the actual path to your Centreon user scripts directory in case you have changed it.
# 

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import argparse

def send_centreon_alert_email(notify_type, 
    host_name, host_alias, host_state, host_address, host_output, 
    recipient_email, totalup, totaldown, duration, date, time):
    # SMTP server configuration
    smtp_server = "smtp.office365.com"  # Replace with your SMTP server. e.g., smtp.office365.com
    smtp_port = "587"  # Replace with your SMTP port, e.g., 587 for TLS
    sender_email = ""  # Replace with your email
    sender_password = ""  # Replace with your email password
    url = "" # This should be the URL of your Centreon instance, will be used to link to host details in the email
    url_image = "" # URL of the image to be included in the email, e.g., a company logo

    # Define color based on host state
    if host_state == "OK":
        color = "green"
    elif host_state == "WARNING":
        color = "orange"
    elif host_state == "CRITICAL" or host_state == "DOWN":
        color = "red"
    else:
        color = "gray"  # Default color for unknown statuses

    # Email content
    subject = f"Host {host_name} status is {host_state}"
    html_content = f"""
        <html>
            <body>
                <table border=0 width='98%' cellpadding=0 cellspacing=0>
                    <tr>
                        <td valign='top'>
                        <br/>
                            <img width="216" height="85" src='{url_image}'> 
                        </td>
                    </tr>
                </table>

                <br/>

                <table border=0 cellpadding=0 cellspacing=0 width='98%'>";               
                    <tr bgcolor={color}>
                        <td width='140'><b><font color=#ffffff>Host: </font></b></td>
                        <td><font color=#ffffff><b> {notify_type} [{host_state}]</b></font></td>
                    </tr> 
                    <tr bgcolor=#eeeeee>
                        <td><b>Hostname: </b></td>
                        <td><b><a href='{url}/centreon/main.php?p=20202&o=hd&host_name={host_name}'>{host_alias}</a></b></td>
                    </tr>
                    <tr bgcolor=#fefefe>
                        <td><b>IP: </b></td>
                        <td><b>{host_address}</b></td>
                    </tr>
                    <tr bgcolor=#eeeeee>
                        <td><b>Date/time: </b></td>
                        <td>{date} {time}</td>
                    </tr>
                    <tr bgcolor=#fefefe>
                        <td><b>Aditional Info: </b></td>
                        <td><b>{host_output}</b></td>
                    </tr>
                    <tr bgcolor=#eeeeee>
                        <td><b>Total Hosts Up: </b></td>
                        <td><b>{totalup}</b></td>
                    </tr>
                    <tr bgcolor=#fefefe>
                        <td><b>Total Hosts Down: </b></td>
                        <td><b>{totaldown}</b></td>
                    </tr>
                    <tr bgcolor=#fefefe>
                        <td><i>Last status</i> duration: </td>
                        <td><font color=#CC0000><b>{duration}</b></font></td>
                    </tr> 
                </table>
            </body>
        </html> 
    """

    # Create the email message
    message = MIMEMultipart("alternative")
    message["Subject"] = subject # Set the email subject
    message["From"] = sender_email # Set the sender email
    message["To"] = recipient_email # Set the recipient email
    message.attach(MIMEText(html_content, "html"))

    try:
        # Connect to the SMTP server and send the email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Secure the connection
            server.login(sender_email, sender_password) # Log in to the SMTP server
            server.sendmail(sender_email, recipient_email, message.as_string()) # Send the email
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Send Centreon alert email.")
    parser.add_argument("--notify_type", required=True, help="Notification type")
    parser.add_argument("--host_name", required=True, help="Host name")
    parser.add_argument("--host_alias", required=True, help="Host alias")
    parser.add_argument("--host_state", required=True, help="Host state")
    parser.add_argument("--host_address", required=True, help="Host address")
    parser.add_argument("--host_output", required=True, help="Host output")
    parser.add_argument("--recipient_email", required=True, help="Contact email")
    parser.add_argument("--totalup", required=True, help="Total hosts up")
    parser.add_argument("--totaldown", required=True, help="Total hosts down")
    parser.add_argument("--duration", required=True, help="Duration of the state")
    parser.add_argument("--date", required=True, help="Date of the alert")
    parser.add_argument("--time", required=True, help="Time of the alert")

    args = parser.parse_args()

    # Call the function with parsed arguments
    send_centreon_alert_email(
        args.notify_type, args.host_name, args.host_alias, args.host_state,
        args.host_address, args.host_output, args.recipient_email,
        args.totalup, args.totaldown, args.duration,
        args.date, args.time
    )