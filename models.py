from django.db import models
from django.db.models.fields.files import ImageFieldFile
from PIL import Image
from os import path
from django.conf import settings
from django.db.models.signals import pre_save, post_save

def optimize_images(sender, **kwargs):
    model = kwargs.get("instance", None)
    if model is not None and isinstance(model, models.Model):
        for attribute in model.__dict__.keys():
            #print(getattr(model_class, attribute, None))
            attr_val = getattr(model, attribute)
            attr_type = type(attr_val)
            if attr_type is ImageFieldFile or issubclass(attr_type, ImageFieldFile):
                attr_val = path.join(settings.MEDIA_ROOT, str(attr_val))
                if path.exists(attr_val) and path.isfile(attr_val):
                    with Image.open(str(attr_val)) as image:
                        image.resize(image.size, resample=4)
                        image.save(str(attr_val), optimize=True, quality=25)
            #print(type(getattr(model, attribute)))
            #print(isinstance(getattr(model, attribute), models.ImageField))

post_save.connect(optimize_images)
# Create your models here.
