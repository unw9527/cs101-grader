import nbformat
import os
from nbclient.exceptions import CellExecutionError
from nbconvert.preprocessors import ExecutePreprocessor
from tqdm import tqdm

class Grader:
    def __init__(self, num_q: int, student_dir: str, test_file: str):
        self.num_q = num_q
        self.student_dir = student_dir
        self.test_file = test_file
        self.err_msg = ''
        with open(self.test_file, 'r') as f:
            tests = nbformat.read(f, nbformat.NO_CONVERT)
        self.tests = tests['cells']
    
    
    def clean_and_add_tests(self, filename: str) -> nbformat.notebooknode.NotebookNode:
        """Remove redundant cells in a notebook.

        Args:
            filename (str): path to the student file

        Returns:
            nbformat.notebooknode.NotebookNode: the cleaned notebook with tests added. 
                  Empty notebooks indicate errors in students' files
        """
        nb_cleaned = nbformat.from_dict({
                                            "cells": [],
                                            "metadata": {
                                            "language_info": {
                                            "name": "python"
                                            },
                                            "orig_nbformat": 4
                                            },
                                            "nbformat": 4,
                                            "nbformat_minor": 2
                                        })
        with open(filename, 'r') as f:
            try:
                nb_raw = nbformat.read(f, nbformat.NO_CONVERT)
            except (nbformat.reader.NotJSONError, UnicodeDecodeError):
                self.err_msg += 'Not a valid notebook: {}\n'.format(filename)
                # print('not a valid notebook')
                return nb_cleaned
            
        # Only keep the cells that are questions
        for cell in nb_raw['cells']:
            if 'metadata' in cell and 'autograding' in cell['metadata']:
                nb_cleaned['cells'].append(nbformat.from_dict(cell))
        # if nb_cleaned['cells'] == []:
        #     print('empty')
                
        # Check whether the number of questions is correct
        if len(nb_cleaned['cells']) != self.num_q:
            self.err_msg += 'Incorrect number of questions: {}\n'.format(filename)
            print('Incorrect number of questions: expect {}, get {}'.format(self.num_q, len(nb_cleaned['cells'])))
            return nb_cleaned
        
        # Copy the metadata
        # nb_cleaned['metadata'] = nb_raw['metadata']
        
        # Attach student's name
        student_info = {'cell_type': 'code', 'metadata': {}, "outputs": [], 'source': 'student_email = "{}"\n'.format(os.path.basename(filename))}
        nb_cleaned['cells'].insert(0, nbformat.from_dict(student_info))
        
        nb_cleaned['cells'].insert(0, nbformat.from_dict(self.tests[0])) ### Forgot to mark this cell...
        # self.tests.pop(0)
        
        # Add tests
        for cell in self.tests:
            if cell == self.tests[0]:
                continue
            nb_cleaned['cells'].append(nbformat.from_dict(cell))
            
        return nb_cleaned
    
    def execute(self, filename: str) -> None:
        """Execute each cleaned notebook with tests

        Args:
            filename (str): path to the notebook
        """
        nb_cleaned = self.clean_and_add_tests(filename)
        ep = ExecutePreprocessor(timeout=600, kernel_name='python3', allow_errors=True)
        nb_cleaned = nbformat.from_dict(nb_cleaned)
        try:
            # print(nb_cleaned)
            with open('temp.ipynb', 'w') as f:
                nbformat.write(nb_cleaned, f)
            ep.preprocess(nb_cleaned, {'metadata': {'path': '{}'.format(self.student_dir)}})
        except CellExecutionError:
            self.err_msg += '{}\n'.format(filename)
            return
        
    def grading(self) -> None:
        """Grade all files
        """
        # for student_file in tqdm(os.listdir(self.student_dir)):
        #     self.execute(os.path.join(self.student_dir, student_file))
        for root, dirs, filenames in os.walk(self.student_dir):
            print(root)
            for filename in tqdm(filenames):
                if filename.endswith('.ipynb'):
                    self.execute(os.path.join(root, filename))
        if self.err_msg != '':
            print("Here are files that fail to be graded: ")
            print(self.err_msg)
                
if __name__ == "__main__":
    g = Grader(6, 'student_files/lab09', 'lab9_test.ipynb')
    g.grading()
    
    