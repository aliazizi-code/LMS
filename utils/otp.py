import pyotp
from django.core.exceptions import SuspiciousOperation
from django.conf import settings
from utils.cache_manager import CacheManager

OTP_TIMEOUT = settings.OTP["EXPIRATION_TIME_SECONDS"]

class OTPManager:
    @staticmethod
    def get_totp(secret):
        """Returns a TOTP object for the given secret."""
        return pyotp.TOTP(secret)

    @staticmethod
    def store_secret(user_id, secret, prefix='otp_secret'):
        """Store the OTP secret in the cache using CacheManager."""
        try:
            CacheManager.set_new_value(user_id, secret, prefix, OTP_TIMEOUT)
        except SuspiciousOperation as e:
            raise SuspiciousOperation(f"Error storing OTP secret: {e}")

    @staticmethod
    def retrieve_secret(user_id, prefix='otp_secret'):
        """Retrieve the OTP secret from the cache using CacheManager."""
        secret = CacheManager.get_value(user_id, prefix)
        if secret is None:
            raise SuspiciousOperation("OTP secret not found in cache.")
        return secret

    @staticmethod
    def generate_otp(user_id, prefix='otp_secret'):
        """Generate a one-time password (OTP) and store its secret."""

        secret = pyotp.random_base32()
        OTPManager.store_secret(user_id, secret, prefix)
        
        totp = OTPManager.get_totp(secret)
        return totp.now()

    @staticmethod
    def verify_otp(user_id, otp, prefix='otp_secret'):
        """Verify the provided OTP against the stored secret."""
        secret = OTPManager.retrieve_secret(user_id, prefix)
        if secret is None:
            return False

        totp = OTPManager.get_totp(secret)
        valid_window = settings.OTP["VALID_WINDOW"]
        if totp.verify(otp, valid_window=valid_window):
            OTPManager.delete_otp(user_id, prefix)
            return True

        return False

    @staticmethod
    def delete_otp(user_id, prefix='otp_secret'):
        """Delete the stored OTP secret from the cache using CacheManager."""
        try:
            CacheManager.delete_value(user_id, prefix)
        except Exception as e:
            raise SuspiciousOperation(f"Error deleting OTP secret: {e}")


# ==============================================
# Main OTP Function for Password Authentication
# ==============================================

def generate_otp_auth_num(user_id):
    delete_otp_auth_num(user_id)
    """Generate a one-time password (OTP) for authentication."""
    return OTPManager.generate_otp(user_id, prefix='otp_secret_auth_num')

def verify_otp_auth_num(user_id, otp):
    """Verify the provided OTP for authentication."""
    return OTPManager.verify_otp(user_id, otp, prefix='otp_secret_auth_num')

def delete_otp_auth_num(user_id):
    """Delete the stored OTP secret for authentication from the cache."""
    OTPManager.delete_otp(user_id, prefix='otp_secret_auth_num')


# ==============================================
# OTP Functions for Changing Phone Number
# ==============================================

def generate_otp_change_phone(user_id):
    delete_otp_change_phone(user_id)
    return OTPManager.generate_otp(user_id, prefix='otp_secret_change_phone')

def verify_otp_change_phone(user_id, otp):
    return OTPManager.verify_otp(user_id, otp, prefix='otp_secret_change_phone')

def delete_otp_change_phone(user_id):
    OTPManager.delete_otp(user_id, prefix='otp_secret_change_phone')

# =============================================
# OTP Functions for Reset Password
# ==============================================

def generate_otp_reset_password(user_id):
    return OTPManager.generate_otp(user_id, prefix='otp_secret_reset_password')

def verify_otp_reset_password(user_id, otp):
    return OTPManager.verify_otp(user_id, otp, prefix='otp_secret_reset_password')

def delete_otp_reset_password(user_id):
    OTPManager.delete_otp(user_id, prefix='otp_secret_reset_password')