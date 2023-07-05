#from django.contrib.staticfiles.finders import find
import os.path as opath
import re
from functools import cached_property, lru_cache, cache
from os import makedirs
from django_optimizer.dlang.utils import path, string
from django_optimizer.dlang.builtins import *
from django.conf import settings
from django.apps import apps
from django.contrib.staticfiles.finders import AppDirectoriesFinder, get_finder
from django.core.exceptions import SuspiciousFileOperation
from django.template.context import Context, RequestContext
from django.db.models import Model, ManyToManyRel, ManyToOneRel, Manager
from hashlib import md5



class LoadFile():
    """
        This is the entrypoint to dynamic assets loading in python
    """
    content: str = None
    path: str = None
    dynamic_folder = opath.basename(str(settings.DYNAMIC_ROOT).removesuffix(opath.sep)) if hasattr(settings, "DYNAMIC_ROOT") else None
    static_folder = get_finder("django.contrib.staticfiles.finders.AppDirectoriesFinder").source_dir
    relative_path: str = None
    _is_dynamic: bool = False
    app_name: str = ""
    namespace: str = ""
    builtins = {
        "static": {
            "func":d_static,
            "args_no": 1
        },
        "if": {
            "func":d_if,
            "type": 1
        }
    }
    dynamic_extensions = [
        "dcss", "djs"
    ]
    """Place each file generated by this class inside a namespace, this is util for when you are placing too 
    much dynamic content for one kind of data, for example if you have a list of users who has their websites 
    personalized, you may want to serve for each user a different css, then you can use this parameter for 
    that case. Each file generated then for this class will be placed at: 
    %DYNAMIC_ROOT%/%namespace%/%path% 
    where %path% is the path given in parameters or the file name if file were given.
    """
    def __init__(self, data=None, path=None, file=None, context: Context =None, in_app=True, namespace=""):
        self.in_app = in_app
        self.context = context if type(context) is dict else context.flatten()
        self.namespace = (namespace and (re.search("[\w]+", namespace)) or [""])[0]
        self.relative_path = path.removeprefix(opath.sep)
        if data and path:
            self.content = str(data)
            self.path = path
        elif file:
            self.content = str(file.read())
            self.path = path or file.name
        elif path:
            self.path = self._absolute_path(path)
            with open(self.path, "r") as file:
                self.content = str(file.read())
        else:
            raise AttributeError("This is improperly configured please give at least data or file")
        #self.process(context)
    
    def process(self):
        """
            Basic language processing function. 
        """
        keys = self.context.keys() # context vars
        parts = re.findall("%[a-zA-Z]+[^%]+%", self.content) # get dynamic parts 
        if len(parts) > 0:    
            self._is_dynamic = True
            result_context = {}
            for part, index in zip(parts, range(len(parts))):
                result_context[index] = {
                    "from": part,
                    "to": part
                } 
                part = " %s "%part[1:-1] # transform % into white spaces, faster than replace cause we knows where will be %s 
                for key in keys: # first action replace all context keys into the scripted part FIXME: must difference between vars and strings  
                    part = part.replace(" %s "%key, '"%s"'%str(self.context.get(key)))
                part = [part]
                if not self._process_block(part):
                    part = string.d_split(part[0]) # Split separated parts of the scripted dynamic languaged
                    ( # next stop at first True return so once the part is processed it jumps to the next part of the logic
                        self._process_builtins(part) # second action process builtins calls, TODO: Must include sum rest and other math operations
                        or self._process_calls(part) # third process object calls 
                        # fourth process block
                    )
                result_context[index].update({ # Update the result context for once its already done
                    "to": " ".join(part)
                })
            for results in result_context.values():
                self.content = self.content.replace(results.get("from"), results.get("to"))
            # if it is dynamic set up the static version
            self.setup()
            return self

    def _process_block(self, parts:list, **kwargs):
        """
            The block must have a structure like
            %   if condition
                    block_code
                or another_condition
                    another_block
                or another_more_condition
                    another_n_more_contions
                else 
                    do_something_else
                and can_be_omitted
                    do_always_if_true
            %
            How to read the previous
            the if is the instruction the after the white space all is considered a condition the \n is the end of condition
            and the start of the block when an 'or' 'else' or 'and' is found then its respective condition is evaluted if:
            'if' condition == true only evaluate 'and' where condition is true.
            'or' is considered like python 'elif' and must have a condition to evaluate, if you wants no condition then use else
            'or' is not evaluated if the if statement was evaluated to true
            'else' is considered like else in python only one is allowed (but more than one is just ignored)
            'and' works almost like finally in python, read it like:
                evaluate_block
                and
                    do_something nasty here :)
            where evaluate_block is any block starting by an if and any combination of conditional instructions
        """
        processed = False
        block_instruction = parts[0].strip().split(" ", 1)
        if len(block_instruction) == 1:
            return processed
        block_instruction, block = iter(block_instruction) # get the block type
        block_instruction = self.builtins.get(block_instruction, None)
        if block_instruction and block_instruction.get("type", 0) == 1:
            processed = True
            parts[0] = block_instruction.get("func")(
                self, block
            )
        return processed

    def _process_calls(self, parts:list, **kwargs):
        """
            Process Calls behaviours... by the way I'm pretty sure that i could use django template instead of my same template language
            but the actual language is intended to be merged with another one we are creating called sly :-) , xD that and that i dont 
            think on that when i was creating this T_T xD
        """
        processed = False
        for arg, i in zip(parts, range(len(parts))): # must process each given args for the form a.b.c.d etc..
            context_var, *call_path = arg.split(".") # Get context var and the execution path...
            if len(call_path) == 0:
                continue
            context_var:object = self.context.get(context_var, None) # Get the actual value of the context var (i mean the object in the context)
            if context_var is None:
                parts[i] = "null"
                continue
            for call in call_path:
                context_var = getattr(context_var, call, None) or (
                    hasattr(context_var, "get") and context_var.get(call) # use the get api to get the call value, this is
                    # mostly used when dealing with dicts like object a possible problem with this aproach is that if a dict like
                    # have for example a key called get then the retrieved value will be the function because the getattr preceeds
                    # the get call :) 
                )# save the actual call state in the context var
                if context_var is None:
                    parts[i] = "null"
                    return processed
                if callable(context_var) and not issubclass(type(context_var), Manager):
                    context_var = context_var() # if the actual call state is callable then call it, TODO add a parametirazed sep like a stack 
                    # for serving args to call states in the path for example var.call.you:1,2,3 and then each time a callable appears then pop(0) from the
                    # stack one argument to the function
            parts[i] = str(context_var)
            processed = True
        return processed

    def _process_builtins(self, parts: list, **kwargs):
        index = 0
        processed = False
        while True:
            builtin = self.builtins.get(parts[index], False)
            index += 1
            if builtin and builtin.get("type", 0) == 0:
                processed = True
                index_walk = index + builtin.get("args_no", 0)
                temp = builtin.get("func", lambda *args:None)(
                    *parts[index: index_walk]
                )
                if temp is not None:
                    parts[index - 1] = temp
                    del parts[index:index_walk]
                index = index_walk + 1
            if index >= (len(parts) - 1):
                break
        return processed

    def setup(self):
        """
            Write from dynamic file to static file 
            TODO Setup static file with @include tag and context id (a receiver hash describing the dyn)
        """
        static_path = self.get_static_path()
        current_ext = opath.basename(static_path).split(opath.extsep)[1]
        if not(current_ext == "css" or current_ext == "js"):
            # asserts that you are not accidentally overwritting a non static file
            raise ValueError("The given file extension is not either css or js, unkown file extension given (%s)"%current_ext)
        makedirs(opath.dirname(static_path), exist_ok=True) # checks tree for missing folders
        if not (self.in_app and static_path.startswith( # checks if static_path is a subpath of APP STATIC FOLDER if we are working in app root
                opath.join(
                    apps.get_app_config(self.app_name).path,
                    self.static_folder
                )
            ) or (
                static_path.startswith(str(settings.STATIC_ROOT)) # checks if static_path is a subpath of ROOT STATIC FOLDER
            )):
            raise SuspiciousFileOperation(
                "The resulting static file cannot be generated outside static folders this may be a use with this framework please report this")
        LoadFile.commit_file(static_path, self.content)
            

    @staticmethod
    @lru_cache # this is very important as reduce significantly the amount of time the web writes to disk, aslo it use a least recent used algorithm
    # which reduce the memory consumption issue 
    def commit_file(static_path, content):
        with open(static_path, "w") as file: # save the content in ready to serve static folder
            file.write(content)

    def split_css(self, ): 
        # TODO This is an uncomplete but very important feature intended to separate in a dynamic file the dynamic
        # part from the not dynamic part (static) allowing to reducing a huge amount of space by sharing non dynamic parts of a 
        # script between all dynamic parts, the master style must use @include tags for all others part the structure of the folder
        # should be as follows:
        # base_css/
        #   master.css -> with @includes
        #   dynamics.css -> n amount of this type
        # static_css/
        #   parts_1_md5_hash.css -> n parts with its name equal to the md5 hash of the content for reference allowance
        # 
        # master.css code example:
        #   @include 'my_dynamic_1.css'
        #   @include 'my_dynamic_2.css'
        #   @include '../my_static_hash.css'
        #   @include '../my_other_static_hash.css'
        return SplitCss(self.content)

    def _absolute_path(self, path=""):
        return self.find_by_app(path)[1] or opath.join(settings.DYNAMIC_ROOT, path.removeprefix(opath.sep))

    @lru_cache
    def find_by_app(self, path: str):
        for app_name, app_config in apps.app_configs.items():
            on_app_path = opath.join(app_config.path, self.dynamic_folder, path.removeprefix(opath.sep))
            if (
                opath.exists(on_app_path)
            ):
                self.app_name, self.path, self.in_app = app_name, on_app_path, True
                return self.app_name, self.path
        self.in_app = False # Even if you say this file is in an app we cannot find it, so for us is not in app ;) 
        return None, False
        
    @lru_cache
    def get_static_path(self, ):
        # folder_hierarch = self.path.removeprefix(str(settings.DYNAMIC_ROOT)).removeprefix(opath.sep) # Returns folders and subfolders after the DYNAMIC ROOT
        static_path = self.relative_path
        file_ext = opath.basename(static_path).split(opath.extsep)[1]
        static_path = static_path.removesuffix(file_ext) + file_ext[1:] # take off d from extensions resulting on the real extension
        if self.namespace and len(self.namespace) > 0:
            static_path = opath.split(static_path)
            static_path = opath.join(static_path[0], self.namespace, static_path[1])
        if self.in_app:
            return opath.join(apps.get_app_config(self.app_name).path, self.static_folder, static_path)
        else:
            return opath.join(settings.STATIC_ROOT, static_path)
        
    def get_static_url(self, ):
        static_path = self.relative_path
        file_ext = opath.basename(static_path).split(opath.extsep)[1]
        static_path = static_path.removesuffix(file_ext) + file_ext[1:] # take off d from extensions resulting on the real extension
        if self.namespace and len(self.namespace) > 0:
            static_path = opath.split(static_path)
            static_path = opath.join(static_path[0], self.namespace, static_path[1])
        return opath.join(settings.STATIC_URL, static_path)

    @cached_property
    def is_dynamic(self):
        return self._is_dynamic or self.__class__.is_dynamic(self.path)

    @classmethod
    def is_dynamic(cls, path):
        try:
            return path and len(path) > 0 and opath.basename(path).split(opath.extsep)[1] in cls.dynamic_extensions
        except IndexError:
            return False

    def __str__(self):
        return self.content


