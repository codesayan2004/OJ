import os

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.files.base import ContentFile
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from problem.models import Problem
from submission.models import TestCase

MAX_TESTCASES_PER_UPLOAD = 50


def _own_problem(request, pid):
    """Hidden test cases may only be seen or changed by the problem's author
    (or staff). Everyone else gets 403."""
    problem = get_object_or_404(Problem, id=pid)
    if problem.author != request.user and not request.user.is_staff:
        raise PermissionDenied("Only the problem author can manage its test cases.")
    return problem


@login_required
def enter_test_case(request, pid):
    _own_problem(request, pid)
    if request.method == 'POST':
        try:
            count = int(request.POST.get('count', 0))
        except ValueError:
            count = 0
        count = max(1, min(count, MAX_TESTCASES_PER_UPLOAD))
        return redirect('test_case', pid=pid, no=count)
    return render(request, 'no_tc.html', {'pid': pid})


@login_required
def test_case(request, pid, no):
    problem = _own_problem(request, pid)
    no = max(1, min(int(no), MAX_TESTCASES_PER_UPLOAD))
    if request.method == 'POST':
        created = 0
        for i in range(no):
            # Each test case may be uploaded as a file or pasted as text.
            input_file = request.FILES.get(f'input_file_{i}')
            input_text = request.POST.get(f'input_text_{i}')
            output_file = request.FILES.get(f'output_file_{i}')
            output_text = request.POST.get(f'output_text_{i}')

            if not input_file and input_text:
                input_file = ContentFile(input_text.encode('utf-8'), name=f'input_{i}.txt')
            if not output_file and output_text:
                output_file = ContentFile(output_text.encode('utf-8'), name=f'output_{i}.txt')
            if not input_file or not output_file:
                continue  # skip incomplete pairs

            TestCase.objects.create(problem=problem, input_file=input_file, output_file=output_file)
            created += 1
        messages.success(request, f'{created} test case(s) added.')
        return redirect('/myproblems')
    return render(request, 'upload_tc.html', {'cnt': range(no)})


@login_required
def view_test_case(request, pid):
    problem = _own_problem(request, pid)
    testcases = TestCase.objects.filter(problem=problem).order_by('id')
    return render(request, 'view_testcase.html', {'testcases': testcases, 'problem': problem})


@login_required
def download_test_case(request, tc_id, kind):
    """Test-case files are NOT served from /media/ (that would leak hidden
    tests); they are streamed through this view after an author check."""
    tc = get_object_or_404(TestCase, id=tc_id)
    _own_problem(request, tc.problem_id)
    field = tc.input_file if kind == 'input' else tc.output_file
    return FileResponse(field.open('rb'), as_attachment=True,
                        filename=os.path.basename(field.name))


@login_required
@require_POST
def delete_test_case(request, pid, tc_id):
    problem = _own_problem(request, pid)
    test_case = get_object_or_404(TestCase, id=tc_id, problem=problem)
    for f in (test_case.input_file, test_case.output_file):
        if f and os.path.isfile(f.path):
            os.remove(f.path)
    test_case.delete()
    return redirect('view_test_case', pid=pid)
