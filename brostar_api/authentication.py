from rest_framework.authentication import SessionAuthentication


class CustomSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        """Added to bypass the csrf requirement on POST requests"""
        return
