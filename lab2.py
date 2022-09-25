import json
import os
from queue import Empty
from xml.etree.ElementTree import QName
import nbformat
from nbclient.exceptions import CellExecutionError
from nbconvert.preprocessors import ExecutePreprocessor
from tqdm import tqdm


class lab2_grader():
    def __init__(self, student_folder: str):
        self.student_folder = student_folder
        with open('sols/lab2-2021-ans.ipynb', 'r') as f:
            nb_ref = nbformat.read(f, nbformat.NO_CONVERT)
        self.nb_ref = nb_ref
        with open('lab2_sol_clean.json', 'r') as f:
            nb_ref_clean = json.load(f)
        self.nb_ref_clean = nb_ref_clean
        self.grades = {}
        self.err_msg = []

    def rm_redundant_cells(self, filename: str) -> dict:
        student_id = os.path.splitext(os.path.basename(filename))[0]
        with open(filename, 'r') as f:
            try:
                nb_in = nbformat.read(f, nbformat.NO_CONVERT)
            except nbformat.reader.NotJSONError:
                self.grades[student_id] = {}
                self.grades[student_id]['score'] = 0
                self.grades[student_id]['feedback'] = "Invalid file"
                return
        temp = []
        for cell, cell_ref in zip(nb_in['cells'], self.nb_ref['cells']):
            if cell_ref['cell_type'] == 'code':
                if 'source' in cell_ref:
                    if 'points' in cell_ref['source'] or 'assert' in cell_ref['source'] \
                        or 'import' in cell_ref['source'] or 'don\'t change' in cell_ref['source'] \
                            or 'definition' in cell_ref['source']:
                        temp.append(cell)
        nb_in['cells'] = temp
        if not os.path.exists('lab2_clean'):
            os.makedirs('lab2_clean')
        with open(os.path.join('lab2_clean', os.path.splitext(os.path.basename(filename))[0]+ '_clean' + '.ipynb'), 'w') as f:
            nbformat.write(nb_in, f)
        return [student_id, nb_in]
    
    def clean_data(self) -> dict:
        cleaned_student_files = {}
        for root, _, files in os.walk(self.student_folder):
            print('Cleaning data...')
            for name in tqdm(files):
                if 'checkpoint' in name:
                    continue
                student_id, nb = self.rm_redundant_cells(os.path.join(root, name))
                cleaned_student_files[student_id] = nb
        return cleaned_student_files

    def grade(self, nb_out: dict, student_id: str):
        self.grades[student_id] = {}
        self.grades[student_id]['score'] = 20
        self.grades[student_id]['feedback'] = ''
        assert len(nb_out['cells']) == len(self.nb_ref_clean['cells'])
        
        for cell, cell_ref in zip(nb_out['cells'], self.nb_ref_clean['cells']):
            # Only grade those are questions
            if 'question' in cell_ref['metadata']:
                q_num = cell_ref['metadata']['question'][0]
                points = cell_ref['metadata']['question'][1]
            else:
                continue
            # Compare each output
            if 'outputs' in cell:
                flag = 0
                output_ref = cell_ref['outputs'][0]
                if 'text' in output_ref:
                        sols = output_ref['text']
                elif 'data' in output_ref:
                    sols = output_ref['data']['text/plain']
                for output in cell['outputs']:
                    if 'text' in output:
                        student_ans = output['text']
                    elif 'data' in output:
                        student_ans = output['data']['text/plain']
                    try:
                        if sols in student_ans:
                            flag = 1
                            break
                    except UnboundLocalError:
                        # If exception occurs, it means the student didn't run the cell
                        self.grades[student_id]['feedback'] += '{}: wrong answer; '.format(q_num)
                        break
                if flag:    
                    self.grades[student_id]['score'] += points
                else:
                    self.grades[student_id]['feedback'] += '{}: wrong answer; '.format(q_num)
    def run(self):
        # print('Grading...')
        cleaned_student_files = self.clean_data()
        print('Grading...')
        for student_id in tqdm(cleaned_student_files):
            ep = ExecutePreprocessor(timeout=600, kernel_name='python3', allow_errors=True)
            try:
                nb_out = ep.preprocess(cleaned_student_files[student_id], {'metadata': {'path': 'lab2_clean'}})
            except CellExecutionError:
                self.err_msg.append('Error executing the notebook "{}".\n\n'.format(cleaned_student_files[student_id]))
                return
            self.grade(nb_out[0], student_id)
        with open('lab2_grades.json', 'w') as f:
            json.dump(self.grades, f, indent=2)
        if self.err_msg != []:
            print("Error: ", self.err_msg)
        
                
if __name__ == '__main__':
    grader = lab2_grader('lab2')
    # grader.clean_data()
    grader.run()