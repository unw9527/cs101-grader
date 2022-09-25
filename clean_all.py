from lab2 import lab2_grader
import os

for root, dirs, files in os.walk('lab02_all'):
    print(root)
    for dir in dirs:
        if dir == 'failed submission' or 'clean' in dir:
            continue
        grader = lab2_grader(os.path.join(root, dir))
        grader.clean_data()