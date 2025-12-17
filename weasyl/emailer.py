import email.policy
import re
from email.mime.text import MIMEText
from smtplib import SMTP

from weasyl import define, macro
from weasyl.config import config_obj


EMAIL_ADDRESS = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\Z")

smtp_host = config_obj.get("smtp", "host", fallback="localhost")
local_hostname = config_obj.get("smtp", "local_hostname", fallback="weasyl-dev.invalid")


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
    message = MIMEText(content.strip(), policy=email.policy.SMTP)
    message["To"] = mailto
    message["From"] = f"Weasyl <{macro.MACRO_EMAIL_ADDRESS}>"
    message["Subject"] = subject

    with SMTP(host=smtp_host, local_hostname=local_hostname) as smtp:
        smtp.starttls()
        smtp.send_message(
            message,
            from_addr=macro.MACRO_EMAIL_ADDRESS,
            to_addrs=[mailto],
        )

    define.metric('increment', 'emails')
