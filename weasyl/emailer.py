import email.policy
import re
import ssl
from email.mime.text import MIMEText
from smtplib import SMTP

from weasyl import define, macro
from weasyl.config import config_obj
from weasyl.rate_limits import GlobalRateLimit
from weasyl.rate_limits import RateLimitId


EMAIL_ADDRESS = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\Z")

smtp_host = config_obj.get("smtp", "host", fallback="localhost")
local_hostname = config_obj.get("smtp", "local_hostname", fallback="weasyl-dev.invalid")
smtp_cert_verify = config_obj.getboolean("smtp", "cert_verify", fallback=True)
smtp_username = config_obj.get("smtp", "username", fallback=None)
smtp_password = config_obj.get("smtp", "password", fallback=None)
if (smtp_username is None) != (smtp_password is None):
    raise RuntimeError("SMTP username and password must be provided together")  # pragma: no cover

mail_out_rate_limit = GlobalRateLimit.parse(RateLimitId.MAIL_OUT, config_obj.get("smtp", "global_rate_limit"))


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
    mail_out_rate_limit.take_one()

    message = MIMEText(content.strip(), policy=email.policy.SMTP)
    message["To"] = mailto
    message["From"] = f"Weasyl <{macro.MACRO_EMAIL_ADDRESS}>"
    message["Subject"] = subject

    with SMTP(host=smtp_host, local_hostname=local_hostname) as smtp:
        ctx = ssl.create_default_context()

        if not smtp_cert_verify:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.VerifyMode.CERT_NONE

        smtp.starttls(context=ctx)

        if smtp_username is not None:
            smtp.login(smtp_username, smtp_password)

        smtp.send_message(
            message,
            from_addr=macro.MACRO_EMAIL_ADDRESS,
            to_addrs=[mailto],
        )

    define.metric('increment', 'emails')
