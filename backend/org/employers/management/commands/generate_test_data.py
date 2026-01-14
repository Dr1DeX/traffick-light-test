import random
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models import Count
from django.utils import timezone
from org.employers.models import Department, Employee


class Command(BaseCommand):
    help = 'Генерирует тестовые данные: 25 отделов в 5 уровнях'

    def handle(self, *args, **options):
        self.stdout.write('Генерация тестовых данных...')
        force = options["force"]
        employees_count = options["count"]

        dept_count = Department.objects.count()
        emp_count = Employee.objects.count()

        if force:
            Employee.objects.all().delete()
            Department.objects.all().delete()
            self.stdout.write("Существующие данные удалены.")
            departments = self.create_departments()
            self.create_employees(departments, employees_count)
            self.stdout.write(self.style.SUCCESS("Данные успешно пересозданы!"))
            return

        if dept_count == 0 and emp_count == 0:
            self.stdout.write("БД пуста, создаём отделы и сотрудников...")
            departments = self.create_departments()
            self.create_employees(departments, employees_count)
            self.stdout.write(self.style.SUCCESS("Данные успешно созданы!"))
            return

        if dept_count > 0 and emp_count == 0:
            self.stdout.write(
                f"Найдено {dept_count} отделов и 0 сотрудников. Генерируем сотрудников для всех отделов..."
            )
            departments = list(Department.objects.all())
            self.create_employees(departments, employees_count)
            self.stdout.write(self.style.SUCCESS("Сотрудники успешно созданы!"))
            return

        departments_without_employees = Department.objects.annotate(
            emp_count=Count("employees")
        ).filter(emp_count=0)

        if departments_without_employees.exists():
            self.stdout.write(
                f"Найдено {departments_without_employees.count()} отделов без сотрудников. Генерируем только для них..."
            )
            self.create_employees(list(departments_without_employees), employees_count)
            self.stdout.write(self.style.SUCCESS("Сотрудники для пустых отделов созданы!"))
        else:
            self.stdout.write(
                self.style.WARNING(
                    f"Отделы ({dept_count}) и сотрудники ({emp_count}) уже существуют."
                )
            )

    def create_departments(self):
        """Создает 25 отделов в 5 уровнях иерархии"""
        departments = []

        # Уровень 1: 1 отдел
        dept1 = Department.objects.create(name="Главное управление")
        departments.append(dept1)

        # Уровень 2: 3 отдела
        for i in range(1, 4):
            dept = Department.objects.create(
                name=f"Управление {i}",
                parent=dept1
            )
            departments.append(dept)

        # Уровень 3: 6 отделов (по 2 на каждый уровень 2)
        level2_depts = [d for d in departments if d.level == 2]
        for parent in level2_depts:
            for i in range(1, 3):
                dept = Department.objects.create(
                    name=f"Отдел {parent.name} - {i}",
                    parent=parent
                )
                departments.append(dept)

        # Уровень 4: 9 отделов
        level3_depts = [d for d in departments if d.level == 3]
        for parent in level3_depts[:6]:
            for i in range(1, 2):
                dept = Department.objects.create(
                    name=f"Сектор {parent.name} - {i}",
                    parent=parent
                )
                departments.append(dept)

        # Уровень 5: 6 отделов
        level4_depts = [d for d in departments if d.level == 4]
        for parent in level4_depts[:6]:
            dept = Department.objects.create(
                name=f"Группа {parent.name}",
                parent=parent
            )
            departments.append(dept)

        return departments

    def create_employees(self, departments):
        """Создает 50,000 сотрудников"""
        positions = [
            "Менеджер", "Разработчик", "Аналитик", "Дизайнер",
            "Тестировщик", "Руководитель", "Специалист", "Консультант"
        ]

        first_names = ["Иван", "Петр", "Сергей", "Александр", "Дмитрий", "Андрей"]
        last_names = ["Иванов", "Петров", "Сидоров", "Смирнов", "Кузнецов", "Попов"]

        employees = []
        batch_size = 1000

        # Получаем path для всех отделов одним запросом
        dept_paths = {}
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, path::text FROM employers_department"
            )
            for row in cursor.fetchall():
                dept_paths[row[0]] = row[1]

        for i in range(100_000):
            dept = random.choice(departments)
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)

            # Получаем path отдела
            dept_path = dept_paths.get(dept.id, str(dept.id))

            employee = Employee(
                full_name=f"{last_name} {first_name} {i}",
                position=random.choice(positions),
                hired_at=timezone.now().date() - timedelta(days=random.randint(0, 3650)),
                salary=Decimal(str(random.randint(30000, 300000))),
                department=dept,
                structure_path=dept_path
            )
            employees.append(employee)

            if len(employees) >= batch_size:
                Employee.objects.bulk_create(employees)
                employees = []
                self.stdout.write(f'Создано {i + 1} сотрудников...')

        if employees:
            Employee.objects.bulk_create(employees)

        self.stdout.write(self.style.SUCCESS(f'Создано {Employee.objects.count()} сотрудников'))
