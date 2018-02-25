# This directory contains hooks

import os.path

datadir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'zoning')

def runHook (slug, hook, data):
    hookFile = os.path.join(os.path.dirname(__file__), slug + '.py')
    if not os.path.exists(hookFile):
        print(f'No hook file found for slug {slug}')
        return data
    else:
        hooks = {}
        with open(hookFile) as hookRaw:
            gl = {k: v for k, v in globals().items()}
            exec(hookRaw.read(), gl, hooks)
        if not hook in hooks:
            print(f'No {hook} hook found for slug {slug}')
            return data
        else:
            print(f'Executing {hook} hook for slug {slug}')
            return hooks[hook](data, datadir)
