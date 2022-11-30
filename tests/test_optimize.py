from django.test import TestCase
from threading import currentThread
from django_optimizer.cron import CronTask
from time import sleep

# Create your tests here.
class OptimizeTest(TestCase):
    def setUp(self, *args, **kwargs):
        pass

    @CronTask.encronlist
    def print_example():
        print("Example 1", currentThread().name)

    @CronTask.encronlist(interval=10000)
    def print_example_2():
        print("Example 2", currentThread().name)

    @CronTask.encronlist(interval=2500, start_after_interval=True)
    def print_example_3(*args, **kwargs):
        print("Example 3", currentThread().name)

    def test_crontask(self, *args,**kwargs):
        """Without sleep the daemon thread stops"""
        crontask: CronTask = CronTask.setup()
        CronTask.crontask.run_all_tasks()
        sleep(10)
        #print(crontask.get_errorlist())
        self.assertTrue(not crontask.has_errors())
    
    def test_cronkill(self, *args, **kwargs):
        crontask: CronTask = CronTask.setup()
        crontask.kill_task("print_example_3")
        self.assertTrue(not crontask.task_exists("print_example_3"))
