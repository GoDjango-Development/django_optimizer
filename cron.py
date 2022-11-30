from threading import Thread, current_thread, RLock, Lock, main_thread, enumerate
from time import sleep, time
from datetime import timedelta
import os


class TaskThread(Thread):

    def __init__(self, *args,**kwargs):
        self.mutex = Lock()
        super().__init__(*args, **kwargs)

    def run(self):
        with self.mutex:
            return super().run()

class CronTask():
    """"
        CronTask is a daemon stalker who stalk in misteryous ways .... O_O Bad luck for you this documentation
        was wrote in a bored moment ...
        Well first than everything ... 
        DO NOT INSTANTIATE THIS DIRECTLY, seriously something bad happens if you do so.... :) 
        This class is thought to be used as an static singleton class ... use CronTask.setup() instead :)
        What this class is not!!! ... is not a goblin, goblin are bads and greeeen, we are daemons, daemons are cute.. ^-^
    """
    crontask = None 
    "The static instance to be used across the lake (the whole program) meaning that this is the static singleton instance"
    __cronlist = {} # For list of crons
    "The list of all scheduled actions"
    __cronhist = {} # For errors in crons
    "The list of all errors in scheduled actions (I think this do not do too much but maybe it does i do not remember)"
    __cronlist_stack = {}
    "The execution stack, meaning each time a method or class is executed its reference is saved here"

    @staticmethod
    def setup(*args, **kwargs):
        """
            Is like a getInstance(In Java) for the singleton purpose (DO NOT INSTANCIATE THIS DIRECTLY the first instance is created 
            in this module apps.py file on the ready method of the AppConfig)
        """
        if CronTask.crontask is None:
            CronTask.crontask = CronTask()
            CronTask.crontask.__cronlist = CronTask.__cronlist
            #CronTask.crontask.__cronhist = CronTask.__cronhist
            CronTask.__cronlist = {}
        return CronTask.crontask

    @staticmethod
    def encronlist(func=None, name=None, interval=5000, exec_once=False,
        start_after_interval=False, break_on_error=False, *args, **kwargs):
        """ 
            Add one function to the cron stack, the difference between using add to stack and add task is that
            one, is executed when yet this class is not instantiated, for example when using decorators, those decorators
            add their function to stack and then those function are processed when this class is instantiated 
        """
        if CronTask.crontask is None:
            adder = CronTask.add_task_tostack
        else:
            adder = CronTask.crontask.add_task
        
        if func is None:
            def wrapper(rfunc,):
                adder(name or rfunc.__name__, rfunc, interval, exec_once=exec_once, start_after_interval=start_after_interval, 
                    break_on_error=break_on_error,
                    *args, **kwargs)
                return rfunc
            return wrapper
        else:
            adder(name or func.__name__, func, interval, exec_once=exec_once, start_after_interval=start_after_interval,
                break_on_error=break_on_error,
                *args, **kwargs)
            return func

    @staticmethod
    def add_task_tostack(task_name, task_method, task_interval, start_after_interval,
        exec_once=False, break_on_error=False,
        *task_args, **task_kwargs):
        """Add a task to the stack"""
        assert task_interval > 0, "Interval must be higher than 0"
        CronTask.__cronlist[task_name] = {
            "method": task_method,
            "args": task_args,
            "kwargs": task_kwargs,
            "interval": task_interval,
            "start_after_interval": start_after_interval,
            "exec_once": exec_once,
            "break_on_error": break_on_error,
            "running": False
        }
        CronTask.__cronhist[task_name] = []

    def add_task(self, task_name: str, task_method: callable, task_interval: int, start_after_interval:bool,
        exec_once:bool=False, break_on_error:bool=False,
        *task_args, **task_kwargs):
        """Add a task to the execution list"""
        assert task_interval > 0, "Interval must be higher than 0"
        self.__cronlist[task_name] = {
            "method": task_method,
            "args": task_args,
            "kwargs": task_kwargs,
            "interval": task_interval,
            "start_after_interval": start_after_interval,
            "exec_once": exec_once,
            "break_on_error": break_on_error,
            "running": False
        }
        self.__cronhist[task_name] = []

    def run_task(self, name, *args, **kwargs):
        """
            Run an especific task in the cronlist
        """
        print("Main Thread is ", main_thread().is_alive(), main_thread()._is_stopped)
        self.__cronlist[name]["_thread_reference"] = TaskThread(
            target=self.__runner,
            args=[name],
            name=name,
            daemon=True
        )
        self.__cronlist[name]["running"] = True
        self.__cronlist[name]["_thread_reference"].start()

    def stop_task(self, name):
        """
            Stop a task by using its name... Take in consideration that we do not actually stop the task we just let the task
            finish their job and then as its running flag is set to false the task is not going to retry again...
            ONLY usefull for cyclic crons, it is not usefull for a single run task
        """
        if name in self.__cronlist.keys():
            if self.__cronlist[name]["_thread_reference"].is_alive():
                self.__cronlist[name]["running"] = False
            del self.__cronlist[name]

    def kill_task(self, name):
        """
            Kill a task by using its name... Take in consideration that unlike stop_task we do actually try to stop the task 
            as soon as possible releasing the mutex who waits and going further
        """
        if (name in self.__cronlist.keys() and self.__cronlist[name]["_thread_reference"].is_alive() and 
            self.__cronlist[name]["running"]):
            self.__cronlist[name]["running"] = False
            if self.__cronlist[name]["_thread_reference"].mutex.locked():
                self.__cronlist[name]["_thread_reference"].mutex.release() # as running is set to false it must ends the thread
            # del self.__cronlist[name] # Should not be uncommented as when the function ends it is delete it by the runner 

    def __runner(self, name):
        exec_once = self.__cronlist[name]["exec_once"]
        while self.__cronlist[name]["running"]:
            if self.__cronlist[name]["start_after_interval"]:
                #print(self.__cronlist[name]["_thread_reference"].mutex)
                #t = time()
                #print("Mutex acquired? ",
                self.__cronlist[name]["_thread_reference"].mutex.acquire(blocking=True, timeout=(int(self.__cronlist[name]["interval"]) or 1000)/1000)
                #)
                #print(timedelta(seconds=time()-t))
            if self.__cronlist.get(name, {}).get("running", False):
                try:
                    #print("Started method exec: ", self.__cronlist[name]["method"], "with args", self.__cronlist[name]["args"], " and ",self.__cronlist[name]["kwargs"])
                    self.__cronlist[name]["method"](
                        *self.__cronlist[name]["args"],
                        **self.__cronlist[name]["kwargs"]
                    )
                    #print("Done method exec")
                except:
                    #print("Throwed an error")
                    if not self.__cronlist[name]["break_on_error"]:
                        continue
                    else:
                        break
                    
            else:
                break
            if exec_once:
                break
            if not self.__cronlist[name]["start_after_interval"]:
                #print(self.__cronlist[name]["_thread_reference"].mutex)
                #t = time()
                self.__cronlist[name]["_thread_reference"].mutex.acquire(blocking=True, 
                    timeout=(int(self.__cronlist[name]["interval"]) or 1000)/1000)
                #print(timedelta(seconds=time()-t))
                #sleep((int(self.__cronlist[name]["interval"]) or 1000)/1000)
        del self.__cronlist[name]

    def get_tasklist(self,):
        return self.__cronlist.copy()

    def get_errorlist(self,):
        return self.__cronhist.copy()
    
    def has_errors(self,):
        for val in self.__cronhist.values():
            return len(val) > 0
        return False

    def run_all_tasks(self,):
        """
            Run all tasks in the lists
        """
        for task_name in self.__cronlist.keys():
            try:
                if not self.__cronlist.get(task_name).get("running", False):
                    self.run_task(task_name)
            except Exception as ex:
                #if self.__cronhist.get(task_name, None) is not None:
                self.__cronhist[task_name].append(ex)

    def task_exists(self, name):
        return self.__cronlist.get(name, None) is not None

#CronTask.setup()

def cron_stats():
    print(f"""
    Debugging STATS:
        executable: {os.sys.executable}
        user: {os.getlogin()}
        platform: {os.sys.platform} {os.sys.version}
        number cpus: {os.cpu_count()}
        load average: {os.getloadavg()}
        process id: {os.getpid()}
        threads: {", ".join(map(lambda x: str(x), enumerate()))}
    """)

def from_hours(amount):
    """
        Convert hours to milliseconds to later use with crons
    """
    return amount * 60 * 60 * 1000

def from_minutes(amount):
    """
        Convert minutes to milliseconds to later use with crons
    """
    return amount * 60 * 1000

def from_seconds(amount):
    """
        Convert seconds to milliseconds to later use with crons
    """
    return amount * 1000

def from_days(amount):
    """
        Convert days to milliseconds to later use with crons
    """
    return amount * 24 * 60 * 60 * 1000

def from_weeks(amount):
    """
        Convert weeks to milliseconds to later use with crons
    """
    return amount * 7 * 24 * 60 * 60 * 1000
