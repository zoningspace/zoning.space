# This directory contains hooks

# Copyright 2018 Zoning.Space contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import os.path

datadir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'zoning')

def runHook (slug, hook, data):
    action = {
        'before': 'preprocessing',
        'after': 'postprocessing'
    }[hook]

    hookFile = os.path.join(os.path.dirname(__file__), slug + '.py')
    if not os.path.exists(hookFile):
        print(f'No hook file found for slug {slug} - not {action} data')
        return data
    else:
        hooks = {}
        with open(hookFile) as hookRaw:
            gl = {k: v for k, v in globals().items()}
            exec(hookRaw.read(), gl, hooks)
        if not hook in hooks:
            print(f'No {hook} hook found for slug {slug} - not {action} data')
            return data
        else:
            print(f'Executing {hook} hook for slug {slug}')
            return hooks[hook](data, datadir)
