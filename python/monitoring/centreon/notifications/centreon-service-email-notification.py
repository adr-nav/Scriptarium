#!/usr/bin/env python3

#
# Author: Adrián Navarro
# Email: contact@adrnav.com
# Last modified: 2025-08-22
#
# Script to send email alerts for services notifications in Centreon
# using the local MTA (sendmail in this case). Make sure your server is configured to send emails.
# You will need to adjust the sender_email variable to match an allowed sender in your MTA configuration.
#
# You can use the command line below to test the script manually, make sure to replace --contact_email with a valid email address:
# python3 /path/to/this/script/centreon-service-email-notification.py --host_name "Notification_test" --host_alias "Notification_test" --host_address "10.20.30.45" --service_output "UNKNOWN: SNMP Table Request: Timeout" --long_date_time "Fri May 2 11:37:40 CEST 2025" --service_desc "SERVICE_TEST" --service_state "UNKNOWN" --contact_email "CHANGE_THIS@mail.com" --service_duration "0d 0h 0m 19s" --total_services_warning "0" --total_services_critical "0" --total_services_unknown "1" --host_group_alias "TEST"
#
# Requirements:
# - Python 3
# - smtplib and email libraries (included in standard library)
# - argparse for command-line argument parsing
# - A local MTA (sendmail) configured to send emails
# 
# You will also need to create a new Notification Command in Centreon (Configuration > Commands > Notifications)
# with the following command line (adjust the path to this script):
# python3 $USER1$/notifications/centreon-service-mail-notification.py --host_name "$HOSTNAME$" --host_alias "$HOSTALIAS$" --host_address "$HOSTADDRESS$" --service_output "$SERVICEOUTPUT$" --long_date_time "$LONGDATETIME$" --service_desc "$SERVICEDESC$" --service_state "$SERVICESTATE$" --contact_email "$CONTACTEMAIL$" --service_duration "$SERVICEDURATION$" --total_services_warning "$TOTALSERVICESWARNING$" --total_services_critical "$TOTALSERVICESCRITICAL$" --total_services_unknown "$TOTALSERVICESUNKNOWN$" --host_group_alias "$HOSTGROUPALIAS$"
#
# Arguments explained:
# --host_name: Name of the host
# --host_alias: Alias of the host
# --host_address: IP address of the host
# --service_output: Additional information about the service state
# --long_date_time: Date and time of the notification
# --service_desc: Description of the service
# --service_state: Current state of the service (e.g., OK, WARNING, CRITICAL, UNKNOWN)
# --service_duration: Duration of the current state
# --contact_email: Email address of the contact to notify
# --total_services_warning: Total number of services in WARNING state
# --total_services_critical: Total number of services in CRITICAL state
# --total_services_unknown: Total number of services in UNKNOWN state
# --host_group_alias: Alias of the host group (In my case I use it to automatically set the customer name in my ticketing system)
#
# Replace $USER1$ with the actual path to your Centreon user scripts directory in case you have changed it.
#

import argparse
import subprocess
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Function to send email
def send_centreon_alert_email(
    host_name, host_alias, host_address, 
    service_output, long_date_time, service_desc, 
    service_state, service_duration, contact_email, 
    total_services_warning, total_services_critical, total_services_unknown, 
    host_group_alias
):
    sender_email = f"centreon-{host_group_alias}@contoso.com"  # CHANGE THIS. Must match an allowed sender in your MTA configuration
    url = "" # URL for your Centreon instance, this is used to create links in the email
    url_image = "" # URL to your logo image

    # Set color based on state
    if service_state == "OK":
        color = "green"
    elif service_state == "WARNING":
        color = "orange"
    elif service_state in ("CRITICAL", "DOWN"):
        color = "red"
    else:
        color = "gray"

    # Create HTML content for the email
    subject = f"Service {service_desc} in host {host_name} status is {service_state}"
    html_content = f"""
    <html>
        <body>
            <img src='{url_image}'>
            <br>
            <br>
            <table border=0 cellpadding=0 cellspacing=0 width=100%>
                <tr bgcolor={color}>
                    <td width='140'><b><font color=#ffffff>Notificacion:</font></b></td>
                    <td><font color=#ffffff><b>{service_state}</b></font></td>
                </tr>
                <tr bgcolor=#eeeeee>
                    <td><b>Host:</b></td>
                    <td><font color=#0000CC><b><a href='{url}/centreon/main.php?p=20202&o=hd&host_name={host_name}'>{host_alias}</a></b></font></td>
                </tr>
                <tr bgcolor=#fefefe>
                    <td><b>Service:</b></td>
                    <td><font color=#0000CC><b><a href='{url}/centreon/main.php?p=20201&o=svcd&host_name={host_name}&service_description={service_desc}'>{service_desc}</a></b></font></td>
                </tr>
                <tr bgcolor=#eeeeee>
                    <td><b>IP:</b></td>
                    <td><font color=#005555><b>{host_address}</b></font></td>
                </tr>
                <tr bgcolor=#fefefe>
                    <td><b>Date/time:</b></td>
                    <td><font color=#005555>{long_date_time}</font></td>
                </tr>
                <tr bgcolor=#eeeeee>
                    <td><b>Aditional Info:</b></td>
                    <td>{service_output}</td>
                </tr>
                <tr bgcolor=#fefefe>
                    <td><b>Notified to:</b></td>
                    <td><font color=#007700><b>{contact_email}</b></font></td>
                </tr>
            </table>
            <br>
            <br>
            <table border=0 cellpadding=0 cellspacing=0 width=100%>
                <tr bgcolor=#000055>
                    <td><b><font color=#FFFFFF>Resumen</font></b></td>
                    <td></td>
                </tr>
                <tr bgcolor=#eeeeee>
                    <td><b>Host Group:</b></td>
                    <td><b>{host_group_alias}</b></td>
                </tr>
                <tr bgcolor=#f6f6ff>
                    <td>Total Warning:</td>
                    <td>{total_services_warning}</td>
                </tr>
                <tr bgcolor=#fffef6>
                    <td>Total Critical:</td>
                    <td>{total_services_critical}</td>
                </tr>
                <tr bgcolor=#f6f6ff>
                    <td>Total Unknown:</td>
                    <td>{total_services_unknown}</td>
                </tr>
                <tr bgcolor=#fffef6>
                    <td>In <i>ALERT</i> for:</td>
                    <td>{service_duration}</td>
                </tr>
            </table>
        </body>
    </html>
    """

    # Create the email message
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = contact_email
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
    parser = argparse.ArgumentParser(description="Send Centreon service alert email without external SMTP.")
    parser.add_argument("--host_name", required=True)
    parser.add_argument("--host_alias", required=True)
    parser.add_argument("--host_address", required=True)
    parser.add_argument("--service_output", required=True)
    parser.add_argument("--long_date_time", required=True)
    parser.add_argument("--service_desc", required=True)
    parser.add_argument("--service_state", required=True)
    parser.add_argument("--service_duration", required=True)
    parser.add_argument("--contact_email", required=True)
    parser.add_argument("--total_services_warning", required=True)
    parser.add_argument("--total_services_critical", required=True)
    parser.add_argument("--total_services_unknown", required=True)
    parser.add_argument("--host_group_alias", required=True)

    args = parser.parse_args()

    send_centreon_alert_email(
        args.host_name, args.host_alias, args.host_address, 
        args.service_output, args.long_date_time, args.service_desc, 
        args.service_state, args.service_duration, args.contact_email, 
        args.total_services_warning, args.total_services_critical, args.total_services_unknown, 
        args.host_group_alias
    )