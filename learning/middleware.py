from django.shortcuts import render
from django.utils.deprecation import MiddlewareMixin
from .authorization import PolicyUnavailable


class PolicyAvailabilityMiddleware(MiddlewareMixin):
    def process_exception(self, request, exception):
        if isinstance(exception, PolicyUnavailable):
            return render(request, '503.html', status=503)
