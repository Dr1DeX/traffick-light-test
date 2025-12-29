from __future__ import annotations

from django.db import connection
from django.db.models.signals import post_save
from django.dispatch import receiver
from org.employers.models import Department


@receiver(post_save, sender=Department)
def update_employees_structure_path(sender, instance, **kwargs):
    """
    Обновляет structure_path у всех сотрудников отдела при изменении path отдела
    """
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT path::text FROM employers_department WHERE id = %s",
            [instance.pk]
        )
        row = cursor.fetchone()
        if row and row[0]:
            new_path = row[0]

            # Обновляем structure_path у всех сотрудников этого отдела и поддерева
            # Используем ltree операторы для поиска всех подотделов
            with connection.cursor() as update_cursor:
                update_cursor.execute(
                    """
                    UPDATE employers_employee
                    SET structure_path = %s::ltree
                    WHERE department_id = %s
                    """,
                    [new_path, instance.pk]
                )
                update_cursor.execute(
                    """
                    UPDATE employers_employee e
                    SET structure_path = %s::ltree
                    FROM employers_department d
                    WHERE e.department_id = d.id
                    AND d.path <@ %s::ltree
                    AND d.id != %s
                    """,
                    [new_path, new_path, instance.pk]
                )
