from rest_framework.authentication import SessionAuthentication


class CustomSessionAuthentication(SessionAuthentication):
    """Added to bypass the csrf requirement on POST requests"""
    def enforce_csrf(self, request):
        """The default SessionAuthentication class includes CSRF protection; this
        module contains a version that doesn't.
        """
        return
