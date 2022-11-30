# django-optimizer
## Image Optimization
Optimize uploaded images on the fly only by installing django_optimizer to installed apps
```py
INSTALLED_APPS = [
    ...,
    "django_optimizer"
]
```
## Cron
It doesnt need to be installed in the installed apps
```py
from django_optimizer.cron import CronTask, from_seconds
@CronTask.encronlist(interval=1000,)
def test_example():
    print("Printed each 1 second")

@CronTask.encronlist(interval=from_seconds(1),)
def test_example2():
    print("Printed each 1 second too!!!")

@CronTask.encronlist(interval=1000, start_after_interval=True)
def test_example3():
    print("Printed after the first second each second")

@CronTask.encronlist(interval=2000, start_after_interval=True)
def test_example3():
    print("Printed after the first 2 seconds each 2 seconds")

```