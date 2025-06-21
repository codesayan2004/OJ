from django.shortcuts import render
from django.http import HttpResponse
from problem.models import Problem
from .models import CodeSubmission
from django.template import loader
from django.contrib import messages
from django.shortcuts import redirect
from django.conf import settings
from pathlib import Path
import subprocess
import uuid, os
from submission.models import TestCase
#from google import genai
import google.generativeai as genai

# Create your views here.

def particular_problem(request, problem_id, *args, **kwargs):
    problem = Problem.objects.get(id=problem_id)
    context = {
        'problem': problem,
        'user_code': kwargs.get('user_code', ''),  # Code submitted by the user
        'user_language': kwargs.get('user_language', 'py'),  # Language selected by the user
        'custom_input': kwargs.get('custom_input', ''),  # Custom input provided by the user
        'result': kwargs.get('result', ''),  # Result of the code execution
    }
    #template = loader.get_template('part_problem.html')
    template = loader.get_template('problem2.html')
    return HttpResponse(template.render(context, request))

def run_particular_problem(request, problem_id):
    if request.user.is_authenticated:
        prob = Problem.objects.get(id=problem_id)
        if request.method == 'POST':
            code = request.POST.get('code')
            language = request.POST.get('language')
            input_data = request.POST.get('custom_input')
            print("Running of code Successful!")
            # Run the code
            result = run(code, language, input_data)
            context = {
                'problem': prob,
                'custom_input': input_data,
                'result': result,
                'user_code': code,
                'user_language': language,
            }
            return particular_problem(request, problem_id, user_code=code, user_language=language, custom_input=input_data, result=result)
            # template = loader.get_template('problem2.html')
            # return HttpResponse(template.render(context, request))

        else:
            context = {
                'problem': prob,
                'user_code': '',  # No code initially
                'user_language': 'py',
            }
            return redirect('/problems/' + str(problem_id) + '/')
            # template = loader.get_template('part_problem.html')
            # return HttpResponse(template.render(context, request))
    else:
        messages.error(request, 'You must be logged in to run code.')
        return redirect('/login')

genai.configure(api_key="AIzaSyBMBYNtPXegEqCdduQ_lGA8UTlo2dUHPMk")
model = genai.GenerativeModel("gemini-1.5-flash")
def ai_review(request, problem_id):
    if request.user.is_authenticated:
        prob = Problem.objects.get(id=problem_id)
        if request.method == 'POST':
            run_particular_problem(request,problem_id)
            code = request.POST.get('code')
            language = request.POST.get('language')
            print("Code for AI:", code)
            prompt = f"Please review the following code and give suggestions for improvemen any bug/error. Dont provide any code. only give short text suggession:\n\n{code}"
            #prompt = "What is Google Gemini"
            response = model.generate_content(prompt)
            template = loader.get_template("ai-review.html")
            context = {
                'problem':prob,
                'ai_feedback': response.text,
                'user_code': code
            }
            return HttpResponse(template.render(context,request))
        else:
            context = {
                'problem': prob,
            }
            template = loader.get_template('problem2.html')
            return HttpResponse(template.render(context, request))
    else:
        messages.error(request, 'You must be logged in to use AI review.')
        return redirect('/login')

    
def normalize(text):
    text = text.strip().replace('\r', '')
    lines = text.split('\n')
    return '\n'.join(' '.join(line.split()) for line in lines)
def submit_code(request, problem_id):
    if request.user.is_authenticated:
        prob = Problem.objects.get(id=problem_id)
        print(prob.title)
        if request.method == 'POST':
            code = request.POST.get('code')
            language = request.POST.get('language')
            input_data = request.POST.get('custom_input')
            # print("Code:", code)
            # print("Language:", language)
            # print("Input Data:", input_data)

            # Save the code submission to the database
            submission = CodeSubmission(
                user=request.user,
                prob=prob,
                code=code,
                language=language,
            )
            submission.save()
            # Run the code
            submission.verdict = "No Test Cases found"
            res = ""
            test_cases = TestCase.objects.filter(problem=prob)
            i=0
            for test_case in test_cases:
                i += 1
                input_data = test_case.input_file.read().decode('utf-8')
                expected_output = test_case.output_file.read().decode('utf-8')
                result = run(code, language, input_data)
                result = normalize(result)
                expected_output = normalize(expected_output)
                # print("Summission Result:")
                # print(result.strip())
                # print(expected_output.strip())
                res = result
                print(result.strip() == expected_output.strip())
                if result.strip() == expected_output.strip():
                    submission.verdict = "Accepted"
                else:
                    submission.verdict = f"Wrong Answer in test {i}"
                    break
            submission.status = "completed"
            # Check for compilation errors
            if submission.verdict != "Accepted":
                if "Error" in res:
                    submission.verdict = "Compilation Error"
                elif "Time Limit Exceeded" in res:
                    submission.verdict = "Time Limit Exceeded"
            print("Submission Successful!")
            # Save the verdict
            submission.save()
            # Redirect to a success page or render a template with the result
            template = loader.get_template('all_my_sub.html')
            sub = CodeSubmission.objects.filter(prob=prob, user=request.user).order_by('-submission_time')
            context = {
                'submissions': sub,
            }
            return HttpResponse(template.render(context, request))
        else:
            problem = Problem.objects.get(id=problem_id)
            template = loader.get_template('part_problem.html')
            context = {
                'problem': problem,
            }
            return HttpResponse(template.render(context, request))
    else:
        messages.error(request, 'You must be logged in to submit code.')
        return redirect('/login')
    
# Real Run code
def run(code, language, input_data):
    project_path = Path(settings.BASE_DIR)
    directories = ["codes", "inputs", "outputs"]

    for directory in directories:
        dir_path = project_path / directory
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
    codes_dir = project_path / "codes"
    inputs_dir = project_path / "inputs"
    outputs_dir = project_path / "outputs"
    unique = str(uuid.uuid4())

    code_file = codes_dir / f"{unique}.{language}"
    input_file = inputs_dir / f"{unique}_input.txt"
    output_file = outputs_dir / f"{unique}_output.txt"
    exe_file = codes_dir / unique
    
    if language == 'java':
        code_file = codes_dir / "Main.java"  # Always Main.java for Java
    else:
        code_file = codes_dir / f"{unique}.{language}"

    # Save code and input to files
    code_file.write_text(code)
    input_file.write_text(input_data)

    try:
        if language == 'cpp':
            exe_path = codes_dir / unique
            compile_cmd = ['g++', str(code_file), '-o', str(exe_path)]
            compile_result = subprocess.run(compile_cmd, capture_output=True, text=True)

            if compile_result.returncode != 0:
                return "Compilation Error:\n" + compile_result.stderr

            try:
                with open(input_file, 'r') as f, open(output_file, 'w') as out_f:
                    exec_result = subprocess.run(
                        [str(exe_path)],
                        stdin=f,
                        stdout=out_f,
                        stderr=subprocess.PIPE,  # capture stderr separately
                        timeout=5
                    )
            except subprocess.TimeoutExpired:
                return "Time Limit Exceeded"
            except Exception as e:
                return f"Unexpected Error: {str(e)}"
        
        elif language == 'c':
            exe_path = codes_dir / unique
            compile_cmd = ['gcc', str(code_file), '-o', str(exe_path)]
            result = subprocess.run(compile_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                return "Compilation Error:\n" + result.stderr
            try:
                with open(input_file, 'r') as f, open(output_file, 'w') as out_f:
                    subprocess.run(
                        [str(exe_path)], stdin=f, stdout=out_f, timeout=5
                    )
            except subprocess.TimeoutExpired:
                return "Time Limit Exceeded"

        elif language == 'py':
            try:
                with open(input_file, 'r') as f, open(output_file, 'w') as out_f:
                    subprocess.run(
                        ['python3', str(code_file)],
                        stdin=f,
                        stdout=out_f,
                        stderr=subprocess.STDOUT,
                        timeout=5  # You can change this as needed
                    )
            except subprocess.TimeoutExpired:
                return "Time Limit Exceeded"
            except Exception as e:
                return f"Runtime Error: {str(e)}"
        elif language == 'java':
            compile_cmd = ['javac', str(code_file)]
            compile_result = subprocess.run(compile_cmd, capture_output=True, text=True)
            if compile_result.returncode != 0:
                return "Compilation Error:\n" + compile_result.stderr

            with open(input_file, 'r') as f, open(output_file, 'w') as out_f:
                subprocess.run(
                    ['java', '-cp', str(codes_dir), 'Main'],
                    stdin=f, stdout=out_f, stderr=subprocess.STDOUT, timeout=5
                )

        elif language == 'js':
            with open(input_file, 'r') as f, open(output_file, 'w') as out_f:
                subprocess.run(
                    ['node', str(code_file)],
                    stdin=f, stdout=out_f, stderr=subprocess.STDOUT, timeout=5
                )
        else:
            return "Unsupported language"
        return output_file.read_text()
    except Exception as e:
        return f"Runtime Error! : {str(e)}"
    finally:
        # Clean up temporary files
        for file in [code_file, input_file, output_file, exe_file]:
            try:
                if file.exists():
                    file.unlink()
            except Exception as e:
                print(f"Warning: Could not delete file {file}: {e}")

def my_submission(request):
    if request.user.is_authenticated:
        sub = CodeSubmission.objects.filter(user=request.user).order_by('-submission_time')
        context = {
            'submissions': sub,
        }
        template = loader.get_template('all_my_sub.html')
        return HttpResponse(template.render(context, request))
    else:
        messages.error(request, 'You must be logged in to view your submissions.')
        return redirect('/login')