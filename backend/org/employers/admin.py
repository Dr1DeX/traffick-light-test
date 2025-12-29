from django.contrib import admin
from .models import Department, Employee


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'level', 'path', 'employees_count']
    list_filter = ['level', 'parent']
    search_fields = ['name', 'path']
    readonly_fields = ['level', 'path']
    ordering = ['path']

    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'parent')
        }),
        ('Системная информация', {
            'fields': ('level', 'path'),
            'classes': ('collapse',)
        }),
    )

    def employees_count(self, obj):
        """Количество сотрудников в отделе"""
        return obj.employees.count()

    employees_count.short_description = 'Сотрудников'


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'position', 'department', 'hired_at', 'salary']
    list_filter = ['department', 'hired_at', 'position']
    search_fields = ['full_name', 'position', 'department__name']
    readonly_fields = ['structure_path']
    date_hierarchy = 'hired_at'

    fieldsets = (
        ('Основная информация', {
            'fields': ('full_name', 'position', 'department')
        }),
        ('Работа', {
            'fields': ('hired_at', 'salary')
        }),
        ('Системная информация', {
            'fields': ('structure_path',),
            'classes': ('collapse',)
        }),
    )
