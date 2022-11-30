from django.conf import settings
from os.path import join
from django_optimizer.dlang.utils.string import d_split, d_filter_until, d_find_all_calls

def d_if(loader, block: str): # FIXME This can be optimized am too sleepy right now to think how U_U 
    block = "if " + block
    block = list(map(lambda sentence: sentence.strip(), block.split("\n")))
    index = 0
    res = ""
    block_conditionals = ["if", "or", "else", "and"]
    param_cond_index = 2
    unparam_cond_index = 2
    while True:
        sentence = block[index] # process conditional sentence 
        part = sentence.split() # split sentence into parts
        loader._process_calls(part) # process parts for processor
        #print("evaluating: ", sentence)
        # first time the block is processed is because we are in a condition sentence so set the semaphore on if semaphore is false
        # then ignore next parts of the block until the next conditional sentence
        if index == len(block) - 1:
            return res
        index += 1
        if (part[0] in  block_conditionals[:param_cond_index] and d_and(part[1:]) == "true") \
            or (part[0] in block_conditionals[unparam_cond_index:]): # else or and
            
            # as 'and' is always executed never delete it
            #  
            while True: # process block
                block_sentence = block[index]
                #print("on block evaluating: ", block_sentence)
                if block_sentence.split(" ")[0] in ["if", "or", "else", "and"]:
                    break
                if block_sentence[0] in ["\"", "'"]:
                    block_sentence = d_filter_until(block[index:], stop=block_sentence[0])
                    replacements = {}
                    for call in d_find_all_calls(block_sentence): # split sentence into parts
                        tp = [call] # to process
                        if loader._process_calls(tp): # processed
                            replacements[call] = tp[0]
                        #loader._process_calls(block_sentence) # process parts for processor
                    index += len(block_sentence) - 1
                    block_sentence = "\n".join(block_sentence)
                    for key in replacements.keys():
                        block_sentence = block_sentence.replace(key, replacements.get(key))

                    #print("block sentence now: ", block_sentence)
                    if block_sentence[0] == block_sentence[-1]:
                        res += block_sentence.strip(block_sentence[0])
                #print("Printing res until now, breaking for the next block evaluation: ", res)
                if index == len(block) - 1: # see if we are at the end
                    return res
                index += 1
            # it means i can go in xD this has nothing to do with a real semaphore but the name is cool
            if part[0] in block_conditionals[0:3]: # 'if' or 'or' or 'else'
                param_cond_index = 0
                unparam_cond_index = 0
                del block_conditionals[0:3] # delete or other conditional posibilities
            #print("all conditionals: ", block_conditionals)

def d_and(parts):
    res = False
    #print(parts)
    for part in parts:
        res = part != "null" and part != "false"
    parts[0] = res
    del parts[1:]
    return "true" if res else "false"

def d_static(path):
    return join(settings.STATIC_URL, str(path).strip().strip("'").strip('"').removeprefix("/")) # remove prefix is needed because if / absolute is given then the result is just the absolute part