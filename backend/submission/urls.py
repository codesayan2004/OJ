from django.urls import path
from .views import *;

urlpatterns = [
    path('add_testcase/<int:pid>', enter_test_case, name='tc_cnt'),
    path('add_testcase/<int:pid>/<int:no>', test_case, name='test_case'),
    path('view_testcase/<int:pid>', view_test_case, name='view_test_case'),
    path('delete_testcase/<int:pid>/<int:tc_id>', delete_test_case, name='delete_test_case'),
]