from django.http import HttpRequest
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.exceptions import AuthenticationFailed

from api.models import PersonalAPIKey


class CustomSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request: HttpRequest) -> None:
        """Added to bypass the csrf requirement on POST requests"""
        return


class APIKeyBasicAuthentication(BasicAuthentication):
    """Retrieve a PersonalAPIKey from Basic Auth's password and use it as token.

    The userid should be fixed to "__key__". Only then the password is used as
    an API Key. This Authentication class checks the validity of the key. If it
    is valid, it will be returned so that DRF sets it to request.auth as a
    "token". There is no user logged in (user will stay AnonymousUser).

    Raises:
    - rest_framework.exceptions.AuthenticationFailed: key is invalid or expired

    See also:
    - api.api_keys_permissions.InScope: permission_class that uses request.auth

    """

    fixed_userid = "__key__"

    def authenticate_credentials(self, userid, password, request=None):
        """Interpret the password as a PersonalAPIKey"""
        if userid != self.fixed_userid:
            return

        try:
            prefix, _, _ = password.partition(".")
            api_key = PersonalAPIKey.objects.select_related("user").get(
                prefix=prefix, revoked=False
            )
            if not api_key.is_valid(password):
                raise PersonalAPIKey.DoesNotExist()
        except PersonalAPIKey.DoesNotExist:
            raise AuthenticationFailed("Invalid API Key.")

        if api_key.has_expired:
            raise AuthenticationFailed("API Key has expired.")
        if not api_key.user.is_active:
            raise AuthenticationFailed("User inactive or deleted.")

        api_key.update_last_used()

        return (api_key.user, None)
