import re
from email.mime.text import MIMEText
from smtplib import SMTP

from weasyl import define, macro
from weasyl.config import config_read_setting


EMAIL_ADDRESS = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\Z")


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


def send(mailto, subject, content):
    """Send an e-mail.

    `mailto` must be a normalized e-mail address to send this e-mail to. The
    system email will be designated as the sender.
    """
    message = MIMEText(content.strip())
    message["To"] = mailto
    message["From"] = macro.MACRO_EMAIL_ADDRESS
    message["Subject"] = subject

    # smtp.sendmail() only converts CR and LF (produced by MIMEText and our templates) to CRLF in Python 3. In Python 2, we need this:
    msg_crlf = re.sub(r"\r\n|[\r\n]", "\r\n", message.as_string())

    smtp = SMTP(config_read_setting('host', "localhost", section='smtp'))

    try:
        smtp.sendmail(
            from_addr=macro.MACRO_EMAIL_ADDRESS,
            to_addrs=[mailto],
            msg=msg_crlf,
        )
    finally:
        smtp.quit()

    define.metric('increment', 'emails')
