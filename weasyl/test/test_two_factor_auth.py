from __future__ import absolute_import, unicode_literals

import re
import urllib

import bcrypt
import pyotp
import pytest
from qrcodegen import QrCode

from libweasyl import security
from weasyl import define as d
from weasyl import two_factor_auth as tfa
from weasyl.test import db_utils


recovery_code = "A" * tfa.LENGTH_RECOVERY_CODE
recovery_code_hashed = bcrypt.hashpw(recovery_code.encode('utf-8'), bcrypt.gensalt(tfa.BCRYPT_WORK_FACTOR))


@pytest.mark.usefixtures('db')
def _insert_recovery_code(userid):
    """Insert the test-suite's pre-hashed recovery code"""
    d.engine.execute("""
        INSERT INTO twofa_recovery_codes (userid, recovery_code_hash)
        VALUES (%(userid)s, %(recovery_code_hash)s)
    """, userid=userid, recovery_code_hash=recovery_code_hashed)


@pytest.mark.usefixtures('db')
def _insert_2fa_secret(user_id, tfa_secret_encrypted):
    d.engine.execute("""
        UPDATE login
        SET twofa_secret = %(tfas)s
        WHERE userid = %(userid)s
    """, userid=user_id, tfas=tfa_secret_encrypted)


@pytest.mark.usefixtures('db')
def test_get_number_of_recovery_codes():
    user_id = db_utils.create_user()

    # This /should/ be zero right now, but verify this for test environment sanity.
    assert 0 == d.engine.scalar("""
        SELECT COUNT(*)
        FROM twofa_recovery_codes
        WHERE userid = %(userid)s
    """, userid=user_id)
    assert tfa.get_number_of_recovery_codes(user_id) == 0
    _insert_recovery_code(user_id)
    assert tfa.get_number_of_recovery_codes(user_id) == 1
    d.engine.execute("""
        DELETE FROM twofa_recovery_codes
        WHERE userid = %(userid)s
    """, userid=user_id)
    assert tfa.get_number_of_recovery_codes(user_id) == 0


def test_generate_recovery_codes():
    codes = tfa.generate_recovery_codes()
    assert len(codes) == 10
    for code in codes:
        assert len(code) == tfa.LENGTH_RECOVERY_CODE


def test_store_recovery_codes():
    user_id = db_utils.create_user()
    valid_code_string = "01234567890123456789,02234567890123456789,03234567890123456789,04234567890123456789,05234567890123456789,06234567890123456789,07234567890123456789,08234567890123456789,09234567890123456789,10234567890123456789"

    _insert_recovery_code(user_id)

    # store_recovery_codes() will not accept a string of codes where the total code count is not 10
    invalid_codes = valid_code_string.split(',').pop()
    assert not tfa.store_recovery_codes(user_id, ','.join(invalid_codes))

    # store_recovery_codes() will not accept a string of codes when the code length is not tfa.LENGTH_RECOVERY_CODE
    invalid_codes = "01,02,03,04,05,06,07,08,09,10"
    assert not tfa.store_recovery_codes(user_id, invalid_codes)

    # When a correct code list is provided, the codes will be stored successfully in the database
    assert tfa.store_recovery_codes(user_id, valid_code_string)

    # Extract the current hashed recovery codes
    query = d.engine.execute("""
        SELECT recovery_code_hash
        FROM twofa_recovery_codes
        WHERE userid = %(userid)s
    """, userid=user_id).fetchall()

    # Ensure that the recovery codes can be hashed to the corresponding bcrypt hash
    valid_code_list = valid_code_string.split(',')
    for row in query:
        code_status = False
        for code in valid_code_list:
            if bcrypt.checkpw(code.encode('utf-8'), row['recovery_code_hash'].encode('utf-8')):
                # If the code matches the hash, then the recovery code stored successfully
                code_status = True
                break
        # The code must be valid
        assert code_status


@pytest.mark.usefixtures('db')
def test_is_recovery_code_valid():
    user_id = db_utils.create_user()
    _insert_recovery_code(user_id)

    # Failure: Recovery code is invalid (code was not a real code)
    assert not tfa.is_recovery_code_valid(user_id, "z" * tfa.LENGTH_RECOVERY_CODE)

    # Failure: Recovery codes are tfa.LENGTH_RECOVERY_CODE characters, and fast-fails if not that length.
    assert not tfa.is_recovery_code_valid(user_id, "z" * 19)

    # Success: Recovery code is valid (code is consumed)
    assert tfa.is_recovery_code_valid(user_id, recovery_code)

    # Failure: Recovery code invalid (because code was consumed)
    assert not tfa.is_recovery_code_valid(user_id, recovery_code)

    # Reinsert for case-sensitivity test
    _insert_recovery_code(user_id)

    # Success: Recovery code is valid (because case does not matter)
    assert tfa.is_recovery_code_valid(user_id, recovery_code.lower())


@pytest.mark.usefixtures('db')
def test_init():
    """
    Verify we get a usable 2FA Secret and QRCode from init()
    """
    user_id = db_utils.create_user()
    tfa_secret, tfa_qrcode = tfa.init(user_id)

    computed_uri = pyotp.TOTP(tfa_secret).provisioning_uri(d.get_display_name(user_id), issuer_name="Weasyl")
    qr = QrCode.encode_text(computed_uri, QrCode.Ecc.MEDIUM)
    qr_xml = qr.to_svg_str(4)
    # We only care about the content in the <svg> tags; strip '\n' to permit re.search to work
    qr_svg_only = re.search(r"<svg.*<\/svg>", qr_xml.replace('\n', '')).group(0)
    computed_qrcode = urllib.quote(qr_svg_only)
    # The QRcode we make locally should match that from init()
    assert tfa_qrcode == computed_qrcode
    # The tfa_secret from init() should be 16 characters, and work if passed in to pyotp.TOTP.now()
    assert len(tfa_secret) == 16
    assert len(pyotp.TOTP(tfa_secret).now()) == tfa.LENGTH_TOTP_CODE


@pytest.mark.usefixtures('db')
def test_init_verify_tfa():
    user_id = db_utils.create_user()
    tfa_secret, _ = tfa.init(user_id)

    # Invalid initial verification (Tuple: False, None)
    test_tfa_secret, test_recovery_codes = tfa.init_verify_tfa(user_id, tfa_secret, "000000")
    assert not test_tfa_secret
    assert not test_recovery_codes

    # Valid initial verification
    totp = pyotp.TOTP(tfa_secret)
    tfa_response = totp.now()
    test_tfa_secret, test_recovery_codes = tfa.init_verify_tfa(user_id, tfa_secret, tfa_response)
    assert tfa_secret == test_tfa_secret
    assert len(test_recovery_codes) == 10


@pytest.mark.usefixtures('db')
def test_activate():
    user_id = db_utils.create_user()
    tfa_secret = pyotp.random_base32()
    totp = pyotp.TOTP(tfa_secret)

    # Failed validation between tfa_secret/tfa_response
    assert not tfa.activate(user_id, tfa_secret, "000000")
    # Verify 2FA is not active
    assert not d.engine.scalar("""
        SELECT twofa_secret
        FROM login
        WHERE userid = %(userid)s
    """, userid=user_id)

    # Validation successful, and tfa_secret written into user's `login` record
    tfa_response = totp.now()
    assert tfa.activate(user_id, tfa_secret, tfa_response)
    # The stored twofa_secret must not be plaintext
    stored_secret = d.engine.scalar("""
        SELECT twofa_secret
        FROM login
        WHERE userid = %(userid)s
    """, userid=user_id)
    assert tfa_secret != stored_secret
    # The stored secret must be decryptable to the generated tfa_secret
    assert tfa_secret == tfa._decrypt_totp_secret(stored_secret)


@pytest.mark.usefixtures('db')
def test_is_2fa_enabled():
    user_id = db_utils.create_user()
    tfa_secret = pyotp.random_base32()
    tfa_secret_encrypted = tfa._encrypt_totp_secret(tfa_secret)

    # 2FA is not enabled
    assert not tfa.is_2fa_enabled(user_id)

    # 2FA is enabled
    _insert_2fa_secret(user_id, tfa_secret_encrypted)
    assert tfa.is_2fa_enabled(user_id)


@pytest.mark.usefixtures('db')
def test_deactivate():
    user_id = db_utils.create_user()
    tfa_secret = pyotp.random_base32()
    tfa_secret_encrypted = tfa._encrypt_totp_secret(tfa_secret)
    totp = pyotp.TOTP(tfa_secret)

    # 2FA enabled, deactivated by TOTP challenge-response code
    _insert_2fa_secret(user_id, tfa_secret_encrypted)
    tfa_response = totp.now()
    assert tfa.deactivate(user_id, tfa_response)

    # 2FA enabled, deactivated by recovery code
    _insert_2fa_secret(user_id, tfa_secret_encrypted)
    tfa_response = totp.now()

    _insert_recovery_code(user_id)
    assert tfa.deactivate(user_id, recovery_code)

    # 2FA enabled, failed deactivation (invalid `tfa_response` (code or TOTP token))
    _insert_2fa_secret(user_id, tfa_secret_encrypted)
    assert not tfa.deactivate(user_id, "000000")
    assert not tfa.deactivate(user_id, "a" * tfa.LENGTH_RECOVERY_CODE)


@pytest.mark.usefixtures('db')
def test_force_deactivate():
    user_id = db_utils.create_user()
    tfa_secret = pyotp.random_base32()
    tfa_secret_encrypted = tfa._encrypt_totp_secret(tfa_secret)

    _insert_2fa_secret(user_id, tfa_secret_encrypted)
    _insert_recovery_code(user_id)

    # Verify that force_deactivate() functions as expected.
    assert tfa.is_2fa_enabled(user_id)
    assert tfa.get_number_of_recovery_codes(user_id) == 1

    tfa.force_deactivate(user_id)

    assert not tfa.is_2fa_enabled(user_id)
    assert tfa.get_number_of_recovery_codes(user_id) == 0


@pytest.mark.usefixtures('db')
def test_verify():
    user_id = db_utils.create_user()
    tfa_secret = pyotp.random_base32()
    tfa_secret_encrypted = tfa._encrypt_totp_secret(tfa_secret)
    totp = pyotp.TOTP(tfa_secret)

    _insert_2fa_secret(user_id, tfa_secret_encrypted)
    _insert_recovery_code(user_id)

    # Codes of any other length than tfa.LENGTH_TOTP_CODE or tfa.LENGTH_RECOVERY_CODE returns False
    assert not tfa.verify(user_id, "a" * 5)
    assert not tfa.verify(user_id, "a" * 21)

    # TOTP token matches current expected value (Successful Verification)
    tfa_response = totp.now()
    assert tfa.verify(user_id, tfa_response)

    # TOTP token with space successfully verifies, as some authenticators show codes like
    #   "123 456"; verify strips all spaces. (Successful Verification)
    tfa_response = totp.now()
    # Now split the code into a space separated string (e.g., u"123 456")
    tfa_response = tfa_response[:3] + ' ' + tfa_response[3:]
    assert tfa.verify(user_id, tfa_response)

    # TOTP token does not match current expected value (Unsuccessful Verification)
    assert not tfa.verify(user_id, "000000")

    # Recovery code does not match stored value (Unsuccessful Verification)
    assert not tfa.verify(user_id, "z" * tfa.LENGTH_RECOVERY_CODE)

    # Recovery code matches a stored recovery code (Successful Verification)
    assert tfa.verify(user_id, recovery_code)

    # Recovery codes are case-insensitive (Successful Verification)
    _insert_recovery_code(user_id)
    assert tfa.verify(user_id, recovery_code.lower())

    # Recovery codes are consumed upon use (consumed previously) (Unsuccessful Verification)
    assert not tfa.verify(user_id, recovery_code)

    # When parameter `consume_recovery_code` is set to False, a recovery code is not consumed.
    _insert_recovery_code(user_id)
    assert tfa.get_number_of_recovery_codes(user_id) == 1
    assert tfa.verify(user_id, 'a' * tfa.LENGTH_RECOVERY_CODE, consume_recovery_code=False)
    assert tfa.get_number_of_recovery_codes(user_id) == 1
