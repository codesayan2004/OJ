from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import redirect
from django.template import loader
from problem.models import Problem
from submission.models import TestCase
from django.core.files.base import ContentFile
import os

# Create your views here.
def enter_test_case(request, pid):
    if request.method == 'POST':
        no = request.POST.get('count')
        #test_case(request, pid, no)
        print("From enter tc")
        return redirect('/add_testcase/' + str(pid) + '/' + str(no))
    else:
        template = loader.get_template('no_tc.html')
        context = {
            'pid': pid
        }
        return HttpResponse(template.render(context, request))

def test_case(request, pid, no):
    if request.method == 'POST':
        print("From TC: ", pid)
        problem = Problem.objects.get(id=pid)
        print(problem)

        for i in range(int(no)):
            # Try to get input: file or text
            input_file = request.FILES.get(f'input_file_{i}')
            input_text = request.POST.get(f'input_text_{i}')

            output_file = request.FILES.get(f'output_file_{i}')
            output_text = request.POST.get(f'output_text_{i}')

            # Convert text to file if file not provided
            if not input_file and input_text:
                input_file = ContentFile(input_text.encode('utf-8'), name=f'input_{i}.txt')

            if not output_file and output_text:
                output_file = ContentFile(output_text.encode('utf-8'), name=f'output_{i}.txt')

            if not input_file or not output_file:
                print(f"Missing testcase #{i}. Skipping...")
                continue  # Skip invalid testcases

            # Save to database
            TestCase.objects.create(problem=problem, input_file=input_file, output_file=output_file)
            print(f"TestCase {i} created.")

        return redirect('/myproblems')

    else:
        print("from add tc", pid)
        template = loader.get_template('upload_tc.html')
        context = {
            'cnt': range(int(no)),
        }
        return HttpResponse(template.render(context, request))

def view_test_case(request, pid):
    problem = Problem.objects.get(id=pid)
    testcases = TestCase.objects.filter(problem=problem)
    template = loader.get_template('view_testcase.html')
    context = {
        'testcases': testcases,
        'problem': problem,
    }
    return HttpResponse(template.render(context, request))

def delete_test_case(request, pid, tc_id):
    if (request.method == 'POST'):
        print("From delete tc post")
        print("From delete tc")
        test_case = TestCase.objects.get(id=tc_id)
        if test_case.input_file and os.path.isfile(test_case.input_file.path):
            os.remove(test_case.input_file.path)

        # Delete output file if exists
        if test_case.output_file and os.path.isfile(test_case.output_file.path):
            os.remove(test_case.output_file.path)
        test_case.delete()
        return redirect('/view_testcase/' + str(pid))