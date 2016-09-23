from __future__ import absolute_import

import re
import subprocess
import email.mime.text

from weasyl import define, error, macro


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


def append(mailto, mailfrom, subject, content, displayto=None):
    """Send an e-mail.

    `mailto` must be a list of e-mail addresses to send this e-mail to. If
    `mailfrom` is None, the system email will be designated as the sender.
    Otherwise, `mailfrom` must be a single e-mail address. The 'To' header of the
    e-mail will be a comma-separated list of the `mailto` addresses unless
    `displayto` is not None (in which case it will be set to `displayto`.)
    """

    if not mailfrom:
        mailfrom = macro.MACRO_EMAIL_ADDRESS

    mailfrom = normalize_address(mailfrom)
    subject = subject.strip()
    content = content.strip()

    if not mailto:
        raise error.WeasylError("mailtoInvalid")
    elif not mailfrom:
        raise error.WeasylError("mailfromInvalid")
    elif not content:
        raise error.WeasylError("contentInvalid")

    if not subject:
        subject = "None"

    message = email.mime.text.MIMEText(content.strip())
    if displayto is not None:
        message["To"] = displayto
    else:
        message["To"] = ', '.join(mailto)
    message["From"] = mailfrom
    message["Subject"] = subject

    sendmail_args = ['sendmail'] + list(mailto)
    proc = subprocess.Popen(sendmail_args, stdin=subprocess.PIPE)
    proc.communicate(message.as_string())
    if proc.returncode:
        raise subprocess.CalledProcessError(proc.returncode, sendmail_args)
    define.metric('increment', 'emails')
