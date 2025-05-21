from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import redirect
from django.template import loader
from problem.models import Problem
from submission.models import TestCase
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
        print("From TC: ",pid)
        problem = Problem.objects.get(id=pid)
        print(problem)
        for i in range(no):
            input_data = request.FILES.get('input_' + str(i))
            output_data = request.FILES.get('output_' + str(i))
            print("Input: ", input_data)
            print("Output: ", output_data)
            TestCase.objects.create(problem=problem, input_file=input_data, output_file=output_data)
            print("Instance created")
        return redirect('/myproblems')
    else:
        print("from add tc", pid)
        template = loader.get_template('upload_tc.html')
        context = {
            'cnt' : range(no),
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