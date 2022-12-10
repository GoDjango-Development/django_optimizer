from os.path import sep


def show_divergences(path0: str, path1: str, rfrom_both: str=""):
    """
        Show divergences between two paths, removing third parameter first from both target paths for quicker search
    """
    path0, path1 = path0.removeprefix(rfrom_both).split(sep), path1.removeprefix(rfrom_both).split(sep)
    for path, counter in path0, range(len(path0)):
        if path not in path1:
            yield (path, path1[counter])

