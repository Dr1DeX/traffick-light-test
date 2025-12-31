from django.core.cache import cache
from django.core.paginator import Paginator
from django.db import connection
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.views.generic import TemplateView

from .models import Department, Employee


class DepartmentLTreeView(TemplateView):
    """Отображение древовидной структуры отделов со сотрудниками"""
    template_name = 'employers/department_tree.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Кеширование структуры отделов с количеством сотрудников
        cache_key = 'department_tree_structure'
        cached_data = cache.get(cache_key)

        if cached_data:
            print(f"cached_data: {cached_data}")
            departments_dict, root_departments = cached_data
        else:
            departments = Department.objects.select_related('parent').order_by('path')
            departments_dict = {dept.id: dept for dept in departments}

            # Используем structure_path для подсчета сотрудников каждого отдела
            # Это более эффективно, так как использует GIST индекс на structure_path
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT d.id, COUNT(e.id) as employees_count
                    FROM employers_department d
                    LEFT JOIN employers_employee e ON e.structure_path = d.path
                    GROUP BY d.id
                """)
                counts_dict = {row[0]: row[1] for row in cursor.fetchall()}

            for dept_id, dept in departments_dict.items():
                dept.employees_count = counts_dict.get(dept_id, 0)

            root_departments = [dept for dept in departments if dept.parent_id is None]

            cache.set(cache_key, (departments_dict, root_departments), 300)

        context['departments_dict'] = departments_dict
        context['root_departments'] = root_departments

        return context


class DepartmentEmployeesView(TemplateView):
    """AJAX view для получения пагинированного списка сотрудников отдела(возможно есть смысл кэшировать на уровне L7)"""
    template_name = 'employers/employees_list.html'

    def get(self, request, *args, **kwargs):
        department_id = request.GET.get('department_id')
        page = request.GET.get('page', 1)
        per_page = int(request.GET.get('per_page', 10))
        include_subtree = request.GET.get('include_subtree', 'false').lower() == 'true'

        try:
            department = Department.objects.get(pk=department_id)
        except Department.DoesNotExist:
            return JsonResponse({'error': 'Отдел не найден'}, status=404)

        # Получаем path отдела
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT path::text FROM employers_department WHERE id = %s",
                [department_id]
            )
            row = cursor.fetchone()
            dept_path = row[0] if row and row[0] else str(department_id)

        if include_subtree:
            employees = Employee.objects.extra(
                where=["structure_path <@ %s::ltree"],
                params=[dept_path]
            ).select_related('department').order_by('full_name')
        else:
            employees = Employee.objects.filter(
                structure_path=dept_path
            ).select_related('department').order_by('full_name')

        paginator = Paginator(employees, per_page)

        try:
            page_obj = paginator.page(int(page))
        except:
            page_obj = paginator.page(1)

        context = {
            'employees': page_obj,
            'department': department,
            'page_obj': page_obj,
            'include_subtree': include_subtree,
        }

        # Если это AJAX запрос, возвращаем JSON с HTML
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            html = render_to_string(self.template_name, context, request=request)
            return JsonResponse({
                'html': html,
                'has_previous': page_obj.has_previous(),
                'has_next': page_obj.has_next(),
                'current_page': page_obj.number,
                'num_pages': page_obj.paginator.num_pages,
                'total_count': page_obj.paginator.count,
            })

        return self.render_to_response(context)
