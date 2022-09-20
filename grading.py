import json
import os
import re
import nbformat
from nbclient.exceptions import CellExecutionError
from nbconvert.preprocessors import ExecutePreprocessor
from tqdm import tqdm

class grader():
    def __init__(self, student_dir: str, sols_dir: str, sols_file: str, score: dict):
        self.student_dir = student_dir
        self.sols_dir = sols_dir
        self.sols_file = sols_file
        self.score = score
        self.err_msg = []
    
    def save_err_msg(self):
        '''
        Save error messages to a file
        '''
        with open('error.txt', 'w') as f:
            for msg in self.err_msg:
                f.write(msg)
    
    def clean_data(self, nb: dict)-> dict:
        '''
        Remove redundant fields from nb
        Args: nb: the notebook to be cleaned
        Return: the cleaned notebook
        '''
        new_nb = {}
        question_num = 0
        regexp = re.compile(r'Q[0-9]+ \[')
        for cell in nb['cells']:
            if cell['cell_type'] == 'code' and 'outputs' in cell:
                answer = ''
                for output in cell['outputs']:
                    # there are two kinds of text output
                    if 'text' in output:
                        answer += output['text']
                    elif 'data' in output:
                        answer += output['data']['text/plain']
                if regexp.search(cell['source']):
                    question_num += 1
                new_nb['Q{}'.format(question_num)] = {'answer': answer}
        return new_nb
        
    def run_and_save(self, input_file: str, output_file: str, path: str, timeout: int = 600):
        '''
        Run the notebook and save the output to a json file
        Args: input_file: the name of the notebook file to be executed
              output_file: the name of the output file
              path: the path of the parent directory of the notebook file
              timeout: the maximum time to run the notebook
        Return: None
        '''
        if not os.path.exists('output'):
            os.makedirs('output')
        # if os.path.exists(output_file):
        #     return
        with open(input_file, 'r') as f:
            try:
                nb_in = nbformat.read(f, nbformat.NO_CONVERT)
            except nbformat.reader.NotJSONError:
                self.err_msg.append('Not a valid notebook: {}\n\n'.format(input_file))
                return
        ep = ExecutePreprocessor(timeout=timeout, kernel_name='python3')
        try:
            nb_out = ep.preprocess(nb_in, {'metadata': {'path': path}})
        except CellExecutionError:
            self.err_msg.append('Error executing the notebook "{}".\n\n'.format(input_file))
            return
        with open(output_file, 'w') as f:
            json.dump(self.clean_data(nb_out[0]), f, indent=2)   
            # json.dump(nb_out[0], f, indent=2)
    
    def run_sols(self) -> dict:
        self.run_and_save(input_file = self.sols_file, 
                          output_file = os.path.join('output', 'sols.json'), 
                          path = self.sols_dir)
        with open(os.path.join('output', 'sols.json'), 'r') as f:
            nb = json.load(f)
        return nb
    
    def run_student(self, student_file: str):
        student_id = os.path.splitext(os.path.basename(student_file))[0]
        if not os.path.exists('output/students'):
            os.makedirs('output/students')
        self.run_and_save(input_file = student_file,
                          output_file = os.path.join('output/students', student_id + '.json'),
                          path = self.student_dir)

    def run(self):
        # get sols
        sols = self.run_sols()
        # get each student's answer
        for root, _, files in os.walk(self.student_dir):
            for name in tqdm(files):
                if 'checkpoint' in name:
                    continue
                self.run_student(os.path.join(root, name))
    
    def grade(self, is_run: bool = True):
        if is_run:
            self.run()
        grades = {}
        with open(os.path.join('output', 'sols.json'), 'r') as f:
            sols = json.load(f)
        # compare sols and students' answers
        for root, _, files in os.walk('output/students'):
            for name in tqdm(files):
                with open(os.path.join(root, name), 'r') as f:
                    try:
                        student_ans = json.load(f)
                    except json.decoder.JSONDecodeError:
                        self.err_msg.append('Invalid JSON file "{}".\n\n'.format(os.path.join(root, name)))
                        continue
                student_id = os.path.splitext(name)[0]
                grades[student_id] = {}
                grades[student_id]['score'] = 0
                grades[student_id]['feedback'] = ''
                for qnum in student_ans:
                    if qnum in sols:
                        if student_ans[qnum]['answer'] == sols[qnum]['answer']:
                            grades[os.path.splitext(name)[0]]['score'] += self.score[qnum]
                        else:
                            grades[student_id]['feedback'] += '{}: wrong answer\n'.format(qnum)
                grades[student_id]['score'] /= (sum(self.score.values()) / 100)
        with open('grades.json', 'w') as f:
            json.dump(grades, f, indent=2)
            
        # save all error messages
        self.save_err_msg()
        
if __name__ == '__main__':
    score = {'Q1': 10, 'Q2': 10, 'Q3': 10, 'Q4': 10, 'Q5': 10, 'Q6': 10, 'Q7': 10, 'Q8': 10, 'Q9': 10, 'Q10': 10}
    g = grader(student_dir='lab1', sols_dir='sols', sols_file='sols/lab01-ans-2021.ipynb', score=score)
    g.grade(is_run=True)
