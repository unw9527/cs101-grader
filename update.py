import json
import os
import nbformat
import random

for root, _, files in os.walk('sols'):
    for name in files:
        with open(os.path.join(root, name), 'r') as f:
            try:
                nb_in = nbformat.read(f, nbformat.NO_CONVERT)
            except nbformat.reader.NotJSONError:
                print('Not a json file')
                continue
        for cell in nb_in['cells']:
            if 'metadata' in cell:
                if 'nbgrader' in cell['metadata']:
                    if 'grade_id' in cell['metadata']['nbgrader']:
                        cell['metadata']['nbgrader']['grade_id'] = str(random.getrandbits(16))
        with open(os.path.join(root, name), 'w') as f:
            nbformat.write(nb_in, f)
            
        # break
        # os.system('nbgrader update Desktop/CS101_TA/{}'.format(os.path.join(root, name)))