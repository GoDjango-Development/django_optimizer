import os
import json
import functools
from django_optimizer.dlang.loader import LoadFile
from django_optimizer.middleware import CSPMiddleware as csp
from django.template import Library, Context
from django.contrib.staticfiles.finders import find
from django.conf import settings
from django.db.models.fields.files import ImageFieldFile
from django.contrib.staticfiles.finders import AppDirectoriesFinder, get_finder
from asgiref.sync import async_to_sync
import PIL
register = Library()

@functools.lru_cache
def load_manifest(manifest_path, is_dasset=False):
    """
        Manifests must be in dassets/ or static/ folder 
        returns a json object  
    """
    if not is_dasset: # If not is dynamic asset means it should be a static one
        if settings.DEBUG:
            manifest_path = find(manifest_path)
        else:
            manifest_path = os.path.abspath(os.path.join(settings.STATIC_ROOT, manifest_path))
        # Ensures that the absolute path is a subpath of STATIC_ROOT or if project is in DEBUG go ahead 
        if manifest_path.startswith(str(settings.STATIC_ROOT)) or settings.DEBUG:
            if os.path.exists(manifest_path):
                with open(manifest_path, "r") as manifest:
                    manifest = json.loads(manifest.read())
                    return manifest
            return {}
        else:
            raise PermissionError("You cannot go outside of static folder")
    else:
        raise NotImplementedError("Dynamic Assets are not implemented yet")
    return None

@register.filter
def from_settings(value: str):
    return getattr(settings, value, None)

@register.simple_tag(takes_context=True)
def load_asset(context: Context, asset_name: str, asset_manifest: str=None, is_dynamic=False, 
    files_string="files", prepend_path=True, context_id=None):
    """
        Loads asset name url from asset manifest
    """
    if asset_manifest is not None:
        # Below we are using files_string as is the standard in create react app if you want a different one set it above
        asset_name = load_manifest(manifest_path=asset_manifest, is_dasset=is_dynamic).get(files_string, {}).get(asset_name, None)
    if is_dynamic or LoadFile.is_dynamic(asset_name):
        return LoadFile(path=asset_name, context=context, namespace=context_id).process().get_static_url()
    elif not is_dynamic: # Means is static
        # as URL are very similar to unix url :) testing this in Windows machines may not works, the remove prefix is for allow real joining
        # as os.path.join for some reasons doesnt join anything that starts with /
        if prepend_path:
            return os.path.join(settings.STATIC_URL, asset_name.removeprefix("/"))
        return asset_name

@register.simple_tag()
def generate_nonce(name: str, rule_type: str):
    """
        Generate a nonce to be used in a static dynamic inline script or style
    """
    return csp.nonce_generator(name=name, rule_type=rule_type)

@register.simple_tag()
def load_image(image: ImageFieldFile, aspect_ratio:str, force_resize=False):
    if not (type(image) is ImageFieldFile):
        return load_str_image(image, aspect_ratio)
    aspect_ratio = list(map(lambda x: int(x), aspect_ratio.split("x", 1)))
    if len(aspect_ratio) == 1:
        aspect_ratio *= 2
    folder = os.path.dirname(image.path)
    
    t =  os.path.basename(image.path)[::-1].split(os.path.extsep, 1)
    if not len(t) == 2:
        return "error_loading_image" # str(t, image.path)
    name = t[1][::-1]
    extension = t[0][::-1]
    
    new_name = "{0}_{1}x{2}{3}{4}".format(name, *aspect_ratio, os.path.extsep, extension)
    if not os.path.exists(os.path.join(folder, new_name)):
        with PIL.Image.open(image.path) as thumb:
            thumb: PIL.Image.Image
            thumb = thumb.resize(aspect_ratio) if force_resize else thumb.copy()
            thumb.thumbnail(aspect_ratio)
            thumb.save(os.path.join(folder, new_name))
    return os.path.join(os.path.dirname(image.url), new_name)

@register.simple_tag()
def load_str_image(image_url: str, aspect_ratio:str, force_resize=False):
    f"""
        Used for raw urls, how this is work for example, you give an URL starting with {settings.STATIC_URL} if that is the case
        we search the image in t
    """
    if type(image_url) is ImageFieldFile:
        return load_image(image_url, aspect_ratio)
    aspect_ratio = list(map(lambda x: int(x), aspect_ratio.split("x", 1)))
    if len(aspect_ratio) == 1:
        aspect_ratio *= 2
    is_static = image_url.startswith(settings.STATIC_URL)
    if is_static:
        image_path = get_finder("django.contrib.staticfiles.finders.AppDirectoriesFinder").find(image_url.removeprefix(settings.STATIC_URL).lstrip("/"))
    else:
        image_path = os.path.join(settings.MEDIA_ROOT, image_url)
    folder = os.path.dirname(image_path)
    t =  os.path.basename(image_path)[::-1].split(os.path.extsep, 1)
    if not len(t) == 2:
        return "error_loading_image" # str(t, image.path)
    name = t[1][::-1]
    extension = t[0][::-1]
    new_name = "{0}_{1}x{2}{3}{4}".format(name, *aspect_ratio, os.path.extsep, extension)
    if not os.path.exists(os.path.join(folder, new_name)):
        with PIL.Image.open(image_path) as thumb:
            thumb: PIL.Image.Image
            thumb = thumb.resize(aspect_ratio) if force_resize else thumb.copy()
            thumb.thumbnail(aspect_ratio)
            thumb.save(os.path.join(folder, new_name))
    return os.path.join(settings.STATIC_URL if is_static else settings.MEDIA_URL, os.path.dirname(image_url), new_name)
