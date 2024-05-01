from rest_framework import permissions


class InScope(permissions.BasePermission):
    """Checks whether this request is in scope of the token in request.auth.

    If there is no token or if there is already a user logged in, True will be
    returned (so then, this permission class is equivalent to AllowAll).

    If the token is valid and the action is in scope, logs the user in by
    setting request.user and tls.request.user.

    See also:
    - lizard_nxt.authentication.APIKeyBasicAuthentication: authentication_class
    """

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True  # There is a user so everything is in scope
        if request.auth is None:
            return True  # No APIKey

        # TODO Implement a more fine-grained scopes based on view and method
        if "*:readwrite" not in request.auth.scope.split(" "):
            return False  # Out of scope

        # From now on, the user is 'authenticated' because the operation is now
        # inside the API Key's scope.
        request.user = request.auth.user

        return True
