from django.urls import path

from .views import DepartmentEmployeesView, DepartmentLTreeView

app_name = 'employers'

urlpatterns = [
    path('', DepartmentLTreeView.as_view(), name='department_tree'),
    path('employees/', DepartmentEmployeesView.as_view(), name='department_employees'),
]
