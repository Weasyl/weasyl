"""
Module for handling 2FA-related functions.
"""
from __future__ import absolute_import, unicode_literals

import re
import urllib

import pyotp
from qrcodegen import QrCode

from libweasyl import security
from weasyl import define as d
from weasyl import login

# Number of recovery codes to provide the user
_TFA_RECOVERY_CODES = 10

# This length is configurable as needed; see generate_recovery_codes() below for keyspace/character set
LENGTH_RECOVERY_CODE = 20
# TOTP code length of 6 is the standard length, and is supported by Google Authenticator
LENGTH_TOTP_CODE = 6


def init(userid):
    """
    Initialize 2FA for a user by generating and returning a 2FA secret key.

    When a user opts-in to 2FA, this function generates the necessary 2FA secret,
    and QRcode.

    Parameters:
        userid: The userid of the calling user.

    Returns: A tuple in the format of (tfa_secret, tfa_qrcode), where:
        tfa_secret: The 16 character pyotp-generated secret.
        tfa_qrcode: A QRcode in SVG+XML format containing the information necessary to provision
        a 2FA TOTP entry in an application such as Google Authenticator. Can be dropped as-is into
        a template to render the QRcode.
    """
    tfa_secret = pyotp.random_base32()
    # Get the 2FA provisioning QRCode
    tfa_qrcode = generate_tfa_qrcode(userid, tfa_secret)
    # Return the tuple (2FA secret, 2FA SVG+XML string QRCode)
    return tfa_secret, tfa_qrcode


def generate_tfa_qrcode(userid, tfa_secret):
    """
    Generate a 2FA QRCode on-demand, with the provisioning URI based on the supplied 2FA-secret.

    Used as a helper function for init(), or to regenerate the QRCode from a failed attempt
    at verifying the init()/init_verify_tfa() phases.

    Parameters:
        userid: The userid for the calling user; used to retrieve the username for the provisioning URI.
        tfa_secret: The tfa_secret as generated from init(), initially.

    Returns: A URL-quoted SVG--containing the TOTP provisioning URI--capable of being inserted into
             a data-uri for display to the user.
    """
    totp_uri = pyotp.TOTP(tfa_secret).provisioning_uri(d.get_display_name(userid), issuer_name="Weasyl")
    # Generate the QRcode
    qr = QrCode.encode_text(totp_uri, QrCode.Ecc.MEDIUM)
    qr_xml = qr.to_svg_str(4)
    # We only care about the content in the <svg> tags; strip '\n' to permit re.search to work
    qr_svg_only = re.search(r"<svg.*<\/svg>", qr_xml.replace('\n', '')).group(0)
    return urllib.quote(qr_svg_only)


def init_verify_tfa(userid, tfa_secret, tfa_response):
    """
    Verify that the user has successfully set-up 2FA in Google Authenticator
    (or similar), and generate recovery codes for the user.

    This function is part one of two in enabling 2FA. Successful verification of this phase
    ensures that the user's authentication app is working correctly.

    Parameters:
        userid: The userid of the calling user.
        tfa_secret: The 2FA secret generated from tfa_init(); retrieved from the
        verification page's form information.
        tfa_response: The 2FA challenge-response code to verify against tfa_secret.

    Returns:
        - A tuple of (False, None) if the verification failed; or
        - A tuple in the form of (tfa_secret, generate_recovery_codes(userid)) where:
            tfa_secret: Is the verified working TOTP secret key
            generate_recovery_codes(): Is a set of recovery codes
    """
    totp = pyotp.TOTP(tfa_secret)
    # If the provided `tfa_response` matches the TOTP value, add the value and return recovery codes
    if totp.verify(tfa_response):
        return tfa_secret, generate_recovery_codes()
    else:
        return False, None


def activate(userid, tfa_secret, tfa_response):
    """
    Fully activate 2FA for a given user account, after final validation of the TOTP secret.

    This function is part two--the final part--in enabling 2FA. Passing this step ensures that
    the user has been presented the opportunity to save recovery keys for their account.

    Parameters:
        userid: The userid of the calling user.
        tfa_secret: The 2FA secret generated from tfa_init(); retrieved from the
        verification page's form information.
        tfa_response: The 2FA challenge-response code to verify against tfa_secret.

    Returns: Boolean True if the `tfa_response` corresponds with `tfa_secret`, thus enabling 2FA,
        otherwise Boolean False indicating 2FA has not been enabled.
    """
    totp = pyotp.TOTP(tfa_secret)
    # If the provided `tfa_response` matches the TOTP value, write the 2FA secret into `login`, activating 2FA for `userid`
    if totp.verify(tfa_response):
        d.engine.execute("""
            UPDATE login
            SET twofa_secret = %(tfa_secret)s
            WHERE userid = %(userid)s
        """, tfa_secret=tfa_secret, userid=userid)
        return True
    else:
        return False


def verify(userid, tfa_response, consume_recovery_code=True):
    """
    Verify a 2FA-enabled user's 2FA challenge-response against the stored
    2FA secret.

    Parameters:
        userid: The userid to compare the 2FA challenge-response against.
        tfa_response: User-supplied response string. May be either the Google Authenticator
        (or other app) supplied code, or a recovery code.
        consume_recovery_code:  If set to True, the recovery code is consumed if it is
        valid, otherwise the call to this function is treated as a query to the validity
        of the recovery code. (Default: Boolean True)

    Returns: Boolean True if 2FA verification is successful, Boolean False otherwise.
    """
    # Strip spaces from the tfa_response; they are not valid character, and some authenticator
    #   implementations display the code as "123 456"
    tfa_response = tfa_response.replace(' ', '')
    if len(tfa_response) == LENGTH_TOTP_CODE:
        tfa_secret = d.engine.scalar("""
            SELECT twofa_secret
            FROM login
            WHERE userid = %(userid)s
        """, userid=userid)
        # Validate supplied 2FA response versus calculated current TOTP value.
        totp = pyotp.TOTP(tfa_secret)
        # Return the response of the TOTP verification; True/False
        return totp.verify(tfa_response)
    elif len(tfa_response) == LENGTH_RECOVERY_CODE:
        # Check if `tfa_response` is valid recovery code; consume according to `consume_recovery_code`,
        #  and return True if valid, False otherwise
        return is_recovery_code_valid(userid, tfa_response, consume_recovery_code)
    # Other lengths are invalid; return False
    else:
        return False


def get_number_of_recovery_codes(userid):
    """
    Get and return the number of remaining recovery codes for `userid`.

    Parameters:
        userid: The userid for which to check the count of recovery codes.

    Returns:
        An integer representing the number of remaining recovery codes.
    """
    return d.engine.scalar("""
        SELECT COUNT(*)
        FROM twofa_recovery_codes
        WHERE userid = %(userid)s
    """, userid=userid)


def generate_recovery_codes():
    """
    Generate a set of valid recovery codes.

    Character set is defined by `libweasyl.security`, (ASCII+Numbers), limited to uppercase via
    .upper() for readability.

    Parameters: None

    Returns: A set of length `_TFA_RECOVERY_CODES` where each code is `LENGTH_RECOVERY_CODE`
    characters in length.
    """
    return {security.generate_key(LENGTH_RECOVERY_CODE).upper() for i in range(_TFA_RECOVERY_CODES)}


def store_recovery_codes(userid, recovery_codes):
    """
    Store generated recovery codes into the recovery code table, checking for validity.

    Parameters:
        userid: The userid to save the recovery codes for.
        recovery_codes: Comma separated unicode string of recovery codes.

    Returns: Boolean True if the codes were successfully saved to the database, otherwise
    Boolean False
    """
    # Force the incoming string to uppercase, then split into a list
    codes = recovery_codes.upper().split(',')
    # The list must exist and be equal to the current codes to generate
    if len(codes) != _TFA_RECOVERY_CODES:
        return False
    # Make sure all codes are `LENGTH_RECOVERY_CODE` characters long, as expected
    for code in codes:
        if len(code) != LENGTH_RECOVERY_CODE:
            return False

    # If above checks have passed, clear current recovery codes for `userid` and store new ones
    d.engine.execute("""
        BEGIN;

        DELETE FROM twofa_recovery_codes
        WHERE userid = %(userid)s;

        INSERT INTO twofa_recovery_codes (userid, recovery_code)
        SELECT %(userid)s, unnest(%(tfa_recovery_codes)s);

        COMMIT;
    """, userid=userid, tfa_recovery_codes=list(codes))

    # Verify if the atomic transaction completed; if `code` (one of the new recovery codes) is
    #   valid at this point, the new codes were added
    if is_recovery_code_valid(userid, code, consume_recovery_code=False):
        return True
    else:
        return False


def is_recovery_code_valid(userid, tfa_code, consume_recovery_code=True):
    """
    Checks the recovery code table for a valid recovery code.

    Determine if a supplied recovery code is present in the recovery code table
    for a specified userid. If present, consume the code by deleting the record.
    Case-insensitive, as the code is converted to upper-case before querying
    the database.

    Parameters:
        userid: The userid of the requesting user.
        tfa_code: A candidate recovery code to check.
        consume_recovery_code:  If set to True, the recovery code is consumed if it is
        valid, otherwise the call to this function is treated as a query to the validity
        of the recovery code. (Default: Boolean True)

    Returns: Boolean True if the code was valid and has been consumed, Boolean False, otherwise.
    """
    # Recovery codes must be LENGTH_RECOVERY_CODE characters; fast-fail if this is not the case
    if len(tfa_code) != LENGTH_RECOVERY_CODE:
        return False
    # Check to see if the provided code--converting to upper-case first--is valid and consume if so
    if consume_recovery_code:
        tfa_rc = d.engine.scalar("""
            DELETE FROM twofa_recovery_codes
            WHERE userid = %(userid)s AND recovery_code = %(recovery_code)s
            RETURNING recovery_code
        """, userid=userid, recovery_code=tfa_code.upper())
    else:
        # We only want to see if the code is valid at the moment.
        tfa_rc = d.engine.scalar("""
            SELECT recovery_code
            FROM twofa_recovery_codes
            WHERE userid = %(userid)s AND recovery_code = %(recovery_code)s
        """, userid=userid, recovery_code=tfa_code.upper())
    # Return True if the recovery code was valid, False otherwise
    if tfa_rc:
        return True
    else:
        return False


def is_2fa_enabled(userid):
    """
    Check if 2FA is enabled for a specified user.

    Check the ``login.tfa_secret`` field for the tuple identified by ``userid``. If the field is NULL,
    2FA is not enabled. If it is not null, 2FA is enabled.

    Parameters:
        userid: The userid to check for 2FA being enabled.

    Returns: Boolean True if 2FA is enabled for ``userid``, otherwise Boolean False.
    """
    return d.engine.scalar("""
        SELECT twofa_secret IS NOT NULL
        FROM login
        WHERE userid = %(userid)s
    """, userid=userid)


def deactivate(userid, tfa_response):
    """
    Deactivate 2FA for a specified user.

    Turns off 2FA by nulling-out the ``login.twofa_secret`` field for the user record,
    and clear any remaining recovery codes.

    Parameters:
        userid: The user for which 2FA should be disabled.
        tfa_response: User-supplied response. May be either the Google Authenticator
        (or other app) supplied code, or a recovery code.

    Returns: Boolean True if 2FA was successfully disabled, otherwise Boolean False if the
    verification of `tfa_response` failed (bad challenge-response or invalid recovery code).
    """
    # Sanity checking for length requirement of recovery code/TOTP is performed in verify() function
    if verify(userid, tfa_response):
        # Verification passed, so disable 2FA
        force_deactivate(userid)
        return True
    else:
        return False


def force_deactivate(userid):
    """
    Force-deactivate 2FA for an account.

    Parameters:
        userid: The userid for an account for which to deactivate 2FA.

    Returns: Nothing
    """
    d.engine.execute("""
        BEGIN;

        UPDATE login
        SET twofa_secret = NULL
        WHERE userid = %(userid)s;

        DELETE FROM twofa_recovery_codes
        WHERE userid = %(userid)s;

        COMMIT;
    """, userid=userid)
