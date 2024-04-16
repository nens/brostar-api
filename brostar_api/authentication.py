from django.http import HttpRequest
from rest_framework.authentication import SessionAuthentication


class CustomSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request: HttpRequest) -> None:
        """Added to bypass the csrf requirement on POST requests"""
        return
