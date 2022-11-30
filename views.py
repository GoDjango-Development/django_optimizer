from django.shortcuts import render
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.conf import settings
from functools import cache
from os import path
import json
import http.client
# Create your views here.

@cache
def load_sw_script(): 
    """
        Load the JS and store the response the second time is called it returns the script without opening the file
    """
    response = HttpResponse()
    response.status_code = 404
    
    # If the user wants can set its own SERVICE WORKER script to be loaded by this function 
    sw_path = getattr(settings, "SERVICE_WORKER_PATH", path.join(path.dirname(__file__), "assets/service_worker.js"))
    if path.exists(sw_path):
        with open(sw_path) as sw_script:

            # Add the response status
            response.status_code = 200

            # Add the response content
            response.content = sw_script.read()

            # Add the scope for the service worker
            response.headers["Service-Worker-Allowed"] = getattr(settings, "SERVICE_WORKER_SCOPE", "/")
            
            # Add the content type
            response.headers["Content-Type"] = "text/javascript"

            # Add the content disposition
            response.headers["Content-Disposition"] = 'inline; filename="%s"'%path.basename(sw_path)
    return response

async def get_service_worker_js(request: HttpRequest):
    """
        Use ASGI capabilities to get the service worker script maybe we want to use Http CACHE for this IDK right now... 
    """
    
    return load_sw_script() # As request is not json serializable as it is an object and its hash change for each session request we use cache in another function 

async def verify_reCAPTCHA(request: HttpRequest):
    try:
        conn = http.client.HTTPSConnection("www.google.com")
        payload = 'secret=%s&response=%s'%(getattr(settings, "CAPTCHA_API_TOKEN"), request.POST.get("g-recaptcha-response"))
        headers = {
            "content-type": "application/x-www-form-urlencoded"
        }
        conn.request("POST", "/recaptcha/api/siteverify", payload, headers)
        res = conn.getresponse()
        data = json.loads(res.read().decode("utf-8"))
        if data.get("success"):
            post_then = json.loads(request.POST.get("then", None))
            if post_then is None:
                return HttpResponseBadRequest()
            redirect_url = post_then.get("url", None)
            return resolve(redirect_url).func(request)
        return HttpResponseForbidden("Captcha not passed")
    except Exception as ex:
        print("Exception: %s"%ex)
        return HttpResponseNotModified()

