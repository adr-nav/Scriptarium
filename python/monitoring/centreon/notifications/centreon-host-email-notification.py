#!/usr/bin/env python3

#
# Author: Adrián Navarro
# Email: contact@adrnav.com
# Last modified: 2025-08-22
#
# Script to send email alerts for Centreon host notifications
# using the local MTA (sendmail in this case). Make sure your server is configured to send emails.
# You will need to adjust the sender_email variable to match an allowed sender in your MTA configuration.
# 
# Requirements:
# - Python 3
# - smtplib and email libraries (included in standard library)
# - argparse for command-line argument parsing
# - A local MTA (sendmail) configured to send emails
#
# You will need to adjust the sender_email variable to match an allowed sender in your MTA configuration.
# 
# You will also need to create a new Notification Command in Centreon (Configuration > Commands > Notifications)
# with the following command line (adjust the path to this script):
# python3 $USER1$/notifications/centreon-host-email-notification.py --notify_type "$NOTIFICATIONTYPE$" --host_name "$HOSTNAME$" --host_alias "$HOSTALIAS$" --host_grpalias "$HOSTGROUPALIAS$" --host_state "$HOSTSTATE$" --host_address "$HOSTADDRESS$" --host_output "$HOSTOUTPUT$" --recipient_email "$CONTACTEMAIL$" --totalup "$TOTALHOSTSUP$" --totaldown "$TOTALHOSTSDOWN$" --duration "$HOSTDURATION$" --date "$DATE$" --time "$TIME$"
#
# Arguments explained:
# --notify_type: Type of notification (e.g., PROBLEM, RECOVERY)
# --host_name: Name of the host
# --host_alias: Alias of the host
# --host_grpalias: Alias of the host group (In my case I use it to automatically set the customer name in my ticketing system)
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

import argparse
import subprocess
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Function to send email
def send_centreon_alert_email(notify_type, 
host_name, host_alias, host_grpalias, host_state, 
host_address, host_output, recipient_email, 
totalup, totaldown, duration, 
date, time
):
    sender_email = f"centreon-{host_grpalias}@contoso.com"  # CHANGE THIS. Must match an allowed sender in your MTA configuration
    url = "" # URL to your Centreon instance, e.g., "https://centreon.yourdomain.com"
    url_image = "" # URL to your logo image

    # Set color based on state
    if host_state == "OK":
        color = "green"
    elif host_state == "WARNING":
        color = "orange"
    elif host_state in ("CRITICAL", "DOWN"):
        color = "red"
    else:
        color = "gray"

    # Mail content
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
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = recipient_email
    message.attach(MIMEText(html_content, "html"))

    # Send the email using local sendmail
    try:
        process = subprocess.Popen(
            ["/usr/sbin/sendmail", "-t", "-oi"],
            stdin=subprocess.PIPE
        )
        process.communicate(message.as_string().encode('utf-8'))
    except Exception as e:
        print(f"Error sending email: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send Centreon host alert email without external SMTP.")
    parser.add_argument("--notify_type", required=True)
    parser.add_argument("--host_name", required=True)
    parser.add_argument("--host_alias", required=True)
    parser.add_argument("--host_grpalias", required=True)
    parser.add_argument("--host_state", required=True)
    parser.add_argument("--host_address", required=True)
    parser.add_argument("--host_output", required=True)
    parser.add_argument("--recipient_email", required=True)
    parser.add_argument("--totalup", required=True)
    parser.add_argument("--totaldown", required=True)
    parser.add_argument("--duration", required=True)
    parser.add_argument("--date", required=True)
    parser.add_argument("--time", required=True)

    args = parser.parse_args()

    send_centreon_alert_email(
        args.notify_type, args.host_name, args.host_alias, args.host_grpalias, args.host_state,
        args.host_address, args.host_output, args.recipient_email,
        args.totalup, args.totaldown, args.duration,
        args.date, args.time
    )