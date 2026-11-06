import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from problem.models import Problem
from submission.models import TestCase

from .models import CodeSubmission
from .sandbox import LANGUAGES, judge, run_once

logger = logging.getLogger(__name__)

MAX_CODE_BYTES = 64 * 1024
MAX_INPUT_BYTES = 1024 * 1024


def _read_form(request):
    """Validate the editor form shared by Run, Submit and AI Review."""
    code = request.POST.get('code', '')
    language = request.POST.get('language', 'py')
    custom_input = request.POST.get('custom_input', '')
    if language not in LANGUAGES:
        return None, "Unsupported language."
    if not code.strip():
        return None, "Code is empty."
    if len(code.encode()) > MAX_CODE_BYTES:
        return None, "Code is larger than 64 KB."
    if len(custom_input.encode()) > MAX_INPUT_BYTES:
        return None, "Custom input is larger than 1 MB."
    return (code, language, custom_input), None


def _wants_json(request):
    return request.headers.get('x-requested-with') == 'XMLHttpRequest' \
        or 'application/json' in request.headers.get('accept', '')


def particular_problem(request, problem_id, **kwargs):
    problem = get_object_or_404(Problem, id=problem_id)
    context = {
        'problem': problem,
        'user_code': kwargs.get('user_code', ''),
        'user_language': kwargs.get('user_language', 'py'),
        'custom_input': kwargs.get('custom_input', ''),
        'result': kwargs.get('result', ''),
    }
    return render(request, 'problem2.html', context)


@login_required
def run_particular_problem(request, problem_id):
    """Run code on custom input. The editor calls this with fetch() and shows
    the output instantly; a normal form POST still works as a fallback."""
    if request.method != 'POST':
        return redirect('problem_detail', problem_id=problem_id)
    problem = get_object_or_404(Problem, id=problem_id)
    data, error = _read_form(request)
    if error:
        if _wants_json(request):
            return JsonResponse({'status': 'Invalid', 'output': error}, status=400)
        messages.error(request, error)
        return redirect('problem_detail', problem_id=problem_id)

    code, language, custom_input = data
    result = run_once(code, language, custom_input)
    if result.status == 'System Error':
        logger.error("Sandbox failure: %s", result.stderr)

    if _wants_json(request):
        return JsonResponse({
            'status': result.status,
            'output': result.display(),
            'time_ms': result.time_ms,
        })
    return particular_problem(request, problem.id, user_code=code, user_language=language,
                              custom_input=custom_input, result=result.display())


_gemini_model = None


def _gemini():
    """Configure Gemini lazily from the GEMINI_API_KEY environment variable."""
    global _gemini_model
    if _gemini_model is None and settings.GEMINI_API_KEY:
        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)
        _gemini_model = genai.GenerativeModel(settings.GEMINI_MODEL)
    return _gemini_model


@login_required
def ai_review(request, problem_id):
    problem = get_object_or_404(Problem, id=problem_id)
    if request.method != 'POST':
        return redirect('problem_detail', problem_id=problem_id)
    data, error = _read_form(request)
    if error:
        messages.error(request, error)
        return redirect('problem_detail', problem_id=problem_id)
    code, language, _ = data

    model = _gemini()
    if model is None:
        feedback = "AI review is not configured on this server (GEMINI_API_KEY is missing)."
    else:
        prompt = (
            f"Problem: {problem.title}\n\n{problem.statement}\n\n"
            f"Review the following {LANGUAGES[language]['name']} solution. Point out bugs, "
            "edge cases and complexity issues as short text suggestions. "
            "Do not write any code.\n\n" + code
        )
        try:
            feedback = model.generate_content(prompt).text
        except Exception:  # network/API errors must not crash the page
            logger.exception("Gemini request failed")
            feedback = "AI review is temporarily unavailable. Please try again later."
    return render(request, 'ai-review.html', {
        'problem': problem,
        'ai_feedback': feedback,
        'user_code': code,
        'user_language': language,
    })


@login_required
def submit_code(request, problem_id):
    problem = get_object_or_404(Problem, id=problem_id)
    if request.method != 'POST':
        return redirect('problem_detail', problem_id=problem_id)
    data, error = _read_form(request)
    if error:
        messages.error(request, error)
        return redirect('problem_detail', problem_id=problem_id)
    code, language, _ = data

    submission = CodeSubmission.objects.create(
        user=request.user, prob=problem, code=code, language=language, status='running',
    )

    def tests():
        for tc in TestCase.objects.filter(problem=problem).order_by('id'):
            with tc.input_file.open('rb') as f_in, tc.output_file.open('rb') as f_out:
                yield f_in.read().decode('utf-8', 'replace'), f_out.read().decode('utf-8', 'replace')

    result = judge(code, language, tests())
    submission.verdict = result.verdict
    submission.error_message = result.message
    submission.time_ms = result.max_time_ms
    submission.passed_tests = result.passed
    submission.total_tests = result.total
    submission.status = 'completed'
    submission.save()
    if result.verdict == 'System Error':
        logger.error("Sandbox failure on submission %s: %s", submission.id, result.message)

    subs = CodeSubmission.objects.filter(prob=problem, user=request.user) \
        .select_related('prob').order_by('-submission_time')
    return render(request, 'all_my_sub.html', {'submissions': subs})


@login_required
def my_submission(request):
    subs = CodeSubmission.objects.filter(user=request.user) \
        .select_related('prob').order_by('-submission_time')
    return render(request, 'all_my_sub.html', {'submissions': subs})
