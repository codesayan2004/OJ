"""
Tests for the judge.

    python manage.py test                       # uses SANDBOX_BACKEND from env
    SANDBOX_BACKEND=docker python manage.py test   # real Docker sandbox

Language tests are skipped automatically when a toolchain (or Docker) is
not available on the machine running the tests.
"""
import shutil
import subprocess

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.test import TestCase, override_settings
from django.urls import reverse

from problem.models import Problem
from submission.models import TestCase as ProblemTestCase

from .models import CodeSubmission
from .sandbox import judge, normalize, run_once


def backend_available(tool):
    if settings.SANDBOX_BACKEND == "docker":
        if not shutil.which("docker"):
            return False
        probe = subprocess.run(["docker", "image", "inspect", settings.SANDBOX_IMAGE],
                               capture_output=True)
        return probe.returncode == 0
    return shutil.which(tool) is not None


def needs(tool):
    import unittest
    return unittest.skipUnless(backend_available(tool), f"{tool} / sandbox not available")


class NormalizeTests(TestCase):
    def test_ignores_trailing_whitespace_and_crlf(self):
        self.assertEqual(normalize("1 2  \r\n3\r\n\r\n"), normalize("1 2\n3"))

    def test_keeps_line_structure(self):
        self.assertNotEqual(normalize("1\n2"), normalize("1 2"))


class SandboxTests(TestCase):
    @needs("python3")
    def test_python_ok(self):
        res = run_once("print(int(input()) * 2)", "py", "21\n")
        self.assertEqual(res.status, "OK")
        self.assertEqual(res.stdout.strip(), "42")

    @needs("g++")
    def test_cpp_ok(self):
        code = "#include <iostream>\nint main(){long a,b;std::cin>>a>>b;std::cout<<a+b;}"
        res = run_once(code, "cpp", "2 3")
        self.assertEqual((res.status, res.stdout), ("OK", "5"))

    @needs("gcc")
    def test_c_compilation_error(self):
        res = run_once("int main( { return 0; }", "c", "")
        self.assertEqual(res.status, "Compilation Error")
        self.assertIn("error", res.stderr)

    @needs("python3")
    def test_runtime_error(self):
        res = run_once("raise ValueError('boom')", "py", "")
        self.assertEqual(res.status, "Runtime Error")
        self.assertIn("ValueError", res.stderr)

    @needs("python3")
    def test_program_printing_error_is_not_compilation_error(self):
        res = run_once("print('Error')", "py", "")
        self.assertEqual(res.status, "OK")

    @needs("g++")
    def test_infinite_loop_is_tle(self):
        res = run_once("int main(){volatile long x=0; while(1) x++;}", "cpp", "")
        self.assertEqual(res.status, "Time Limit Exceeded")

    @needs("g++")
    def test_memory_hog_is_mle(self):
        code = ("#include <vector>\n#include <cstdio>\nint main(){std::vector<char*> v;"
                "while(1){char*p=new char[64<<20];for(int i=0;i<(64<<20);i+=4096)p[i]=1;v.push_back(p);}}")
        res = run_once(code, "cpp", "")
        self.assertEqual(res.status, "Memory Limit Exceeded")

    @needs("javac")
    def test_java(self):
        code = ("import java.util.*; public class Main { public static void main(String[] a) {"
                " Scanner s = new Scanner(System.in); System.out.println(s.nextInt() + 1); } }")
        res = run_once(code, "java", "41")
        self.assertEqual((res.status, res.stdout.strip()), ("OK", "42"))

    @needs("node")
    def test_javascript(self):
        code = "const x = require('fs').readFileSync(0, 'utf8').trim(); console.log(Number(x) * 3);"
        res = run_once(code, "js", "14")
        self.assertEqual((res.status, res.stdout.strip()), ("OK", "42"))

    @needs("python3")
    def test_judge_wrong_answer_reports_test_number(self):
        res = judge("print(1)", "py", [("", "1"), ("", "2")])
        self.assertEqual(res.verdict, "Wrong Answer on test 2")
        self.assertEqual((res.passed, res.total), (1, 2))

    @needs("python3")
    def test_judge_accepted(self):
        res = judge("print(int(input())+1)", "py", [("1", "2"), ("41", "42")])
        self.assertEqual(res.verdict, "Accepted")


@needs("docker")
class DockerIsolationTests(TestCase):
    """Only meaningful with SANDBOX_BACKEND=docker."""

    def setUp(self):
        if settings.SANDBOX_BACKEND != "docker":
            self.skipTest("docker backend not enabled")

    def test_no_network(self):
        code = "import socket\nsocket.create_connection(('1.1.1.1', 80), timeout=2)\nprint('connected')"
        res = run_once(code, "py", "")
        self.assertNotIn("connected", res.stdout)
        self.assertEqual(res.status, "Runtime Error")

    def test_cannot_write_outside_tmp(self):
        res = run_once("open('/etc/hacked', 'w').write('x')", "py", "")
        self.assertEqual(res.status, "Runtime Error")

    def test_runs_as_nobody(self):
        res = run_once("import os; print(os.getuid())", "py", "")
        self.assertEqual(res.stdout.strip(), "65534")

    def test_fork_bomb_is_contained(self):
        code = "import os\nwhile True:\n    os.fork()"
        res = run_once(code, "py", "")
        self.assertNotEqual(res.status, "OK")


class ViewTests(TestCase):
    def setUp(self):
        self.author = User.objects.create_user("author", password="pw12345!")
        self.other = User.objects.create_user("other", password="pw12345!")
        self.problem = Problem.objects.create(
            title="Double", statement="Print 2n", sample_in="1", sample_out="2",
            tags="math", difficulty="E", author=self.author)
        self.tc = ProblemTestCase.objects.create(
            problem=self.problem,
            input_file=ContentFile(b"21\n", name="in.txt"),
            output_file=ContentFile(b"42\n", name="out.txt"))

    def tearDown(self):
        for f in (self.tc.input_file, self.tc.output_file):
            f.storage.delete(f.name)

    def test_run_requires_login(self):
        resp = self.client.post(f"/problems/{self.problem.id}/run/", {"code": "print(1)", "language": "py"})
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login/", resp["Location"])

    def test_other_user_cannot_view_or_delete_testcases(self):
        self.client.login(username="other", password="pw12345!")
        self.assertEqual(self.client.get(f"/view_testcase/{self.problem.id}").status_code, 403)
        self.assertEqual(self.client.get(f"/testcase/{self.tc.id}/input/download/").status_code, 403)
        self.assertEqual(self.client.post(f"/delete_testcase/{self.problem.id}/{self.tc.id}").status_code, 403)
        self.assertTrue(ProblemTestCase.objects.filter(id=self.tc.id).exists())

    def test_delete_problem_rejects_get(self):
        self.client.login(username="author", password="pw12345!")
        self.assertEqual(self.client.get(f"/delete_problem/{self.problem.id}/").status_code, 405)
        self.assertTrue(Problem.objects.filter(id=self.problem.id).exists())

    def test_missing_problem_is_404(self):
        self.assertEqual(self.client.get("/problems/9999/").status_code, 404)

    @needs("python3")
    def test_ajax_run_returns_json(self):
        self.client.login(username="other", password="pw12345!")
        resp = self.client.post(f"/problems/{self.problem.id}/run/",
                                {"code": "print(int(input())*2)", "language": "py", "custom_input": "4"},
                                HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "OK")
        self.assertEqual(resp.json()["output"].strip(), "8")

    @needs("python3")
    def test_submit_accepted_and_wrong_answer(self):
        self.client.login(username="other", password="pw12345!")
        url = f"/problems/{self.problem.id}/submit/"
        self.client.post(url, {"code": "print(int(input())*2)", "language": "py"})
        self.client.post(url, {"code": "print(0)", "language": "py"})
        verdicts = list(CodeSubmission.objects.order_by("id").values_list("verdict", flat=True))
        self.assertEqual(verdicts, ["Accepted", "Wrong Answer on test 1"])
        self.assertEqual(self.client.get("/leaderboard/").status_code, 200)
