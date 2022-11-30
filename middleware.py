from django.conf import settings
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.utils.deprecation import MiddlewareMixin
from debug_toolbar.middleware import DebugToolbarMiddleware as dtm
from time import thread_time_ns
from asgiref.sync import async_to_sync
from hashlib import sha256

class CSPMiddleware(MiddlewareMixin):
    default_csp = (
        "default-src 'self';" 
        "script-src 'self';"
        "connect-src 'self';"
        "font-src 'self';"
        "frame-src 'self';" 
        "manifest-src 'self';" 
        "media-src 'self';" 
        "style-src 'self';"
        "img-src 'self';"
        "worker-src 'self';"
        "child-src 'none';"
        "object-src 'none';"
        #"report-uri http://localhost:8000/csp_report/"
    )
    _csp_stack = dict()
    "This stack is cleaned each time a response is given"
    
    csp: dict = getattr(settings, "CONTENT_SECURITY_POLICY", None)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    strict_dynamic = False

    @classmethod
    def nonce_generator(cls, name: str, rule_type: str):
        """
            Use last three digits of nanoseconds for major entropy also use name for a not known entropy
            Each iteration thread_time_ns is different so it should be difficult enough for someone to guess what will be the response 
        """
        nonce = sha256("".join(chr(thread_time_ns()%1000^byte) for byte in name.encode()).encode()).hexdigest()
        for rule in rule_type.split(): # Split using whitespaces in rule type this is useful when you want to add the same nonced script to various CSP rules
            rule_name = "%s-src"%rule
            if rule_name in cls.csp: # If the rule is currently in the policies
                cls._csp_stack[rule_name] = cls._csp_stack.get(rule_name, ()) + ("'nonce-%s'"%nonce,)
        return nonce # For use with HTML ' chars is not escaped so is better off 

    @classmethod
    def settings_to_string(cls):
        if not cls.csp:
            return cls.default_csp
        return "".join("%s %s;"%(rule, " ".join(cls.csp[rule] + cls._csp_stack.get(rule, tuple()))) for rule in cls.csp)

    def process_request(self, request: HttpRequest):
        self.__class__._csp_stack = dict() # Returns the stack to default

    def process_response(self, request: HttpRequest, response: HttpResponse):
        """
            Returns the http response with the Content Security Policy for the requested url
        """
        # response.headers: ResponseHeaders
        if type(response) is HttpResponse:
            response.headers["Content-Security-Policy"] = self.__class__.settings_to_string()
        return response
