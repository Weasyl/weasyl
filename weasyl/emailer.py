from __future__ import absolute_import

import re
import subprocess
import email.mime.text

from weasyl import define, macro


EMAIL_ADDRESS = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


def normalize_address(address):
    """
    Converts an e-mail address to a consistent representation.
    Returns None if the given address is not considered valid.
    """
    address = address.strip()

    if not EMAIL_ADDRESS.match(address):
        return None

    local, domain = address.split("@", 1)

    return "%s@%s" % (local, domain.lower())


def append(mailto, subject, content):
    """Send an e-mail.

    `mailto` must be a normalized e-mail address to send this e-mail to. The
    system email will be designated as the sender.
    """
    message = email.mime.text.MIMEText(content.strip())
    message["To"] = mailto
    message["From"] = macro.MACRO_EMAIL_ADDRESS
    message["Subject"] = subject

    sendmail_args = ['sendmail', '-t']
    proc = subprocess.Popen(sendmail_args, stdin=subprocess.PIPE)
    proc.communicate(message.as_string())
    if proc.returncode:
        raise subprocess.CalledProcessError(proc.returncode, sendmail_args)
    define.metric('increment', 'emails')
