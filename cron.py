from threading import Thread
from time import sleep

__all__ = ("crontask", )

class CronTask():
    __cronlist = {} 
    __cronhist = {}
    __mutex = 0

    def __init__(self,):
        pass
    
    def add_task(self, task_name, task_method, task_interval, *task_args, **task_kwargs):
        assert task_interval > 0, "Interval must be higher than 0"
        self.__cronlist[task_name] = {
            "method": task_method,
            "args": task_args,
            "kwargs": task_kwargs,
            "interval": task_interval,
            "running": False
        }
        self.__cronhist[task_name] = []

    def run_task(self, name):
        self.__runner(name)
        #Thread(target=self.__runner, args=[name, ], name=name).start()

    def __runner(self, name):
        while True:
            self.__cronlist[name]["method"](
                *self.__cronlist[name]["args"], 
                **self.__cronlist[name]["kwargs"]
            )
            sleep((self.__cronlist[name]["interval"] or 1000)/1000)

    def get_tasklist(self,):
        return self.__cronlist.copy()

    def run_all_tasks(self,):
        for task_name in self.__cronlist.keys():
            try:
                self.run_task(task_name)
            except Exception as ex:
                #if self.__cronhist.get(task_name, None) is not None:
                self.__cronhist[task_name].append(ex)

crontask: CronTask = None

if crontask is None:
    crontask = CronTask()

def encronlist(func, interval=5000):
    crontask.add_task(func.__name__, func, interval, )
    return func

@encronlist
def print_example():
    print("example")

def run_example():
    #print(crontask.get_tasklist())
    crontask.run_all_tasks()

#run_example()