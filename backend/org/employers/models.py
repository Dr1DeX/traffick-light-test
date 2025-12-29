from __future__ import annotations

from decimal import Decimal

from django.contrib.postgres.indexes import GistIndex
from django.core.exceptions import ValidationError
from django.db import connection, models, transaction
from django_ltree_field.fields import LTreeField


class Department(models.Model):
    """
    Materialized path на ltree. Глубина ограничена 5 уровнями.
    path: "1.8.42" (цепочка id).
    level: nlevel(path) (для UI/отступов и тд).

    See example: https://patshaughnessy.net/2017/12/14/manipulating-trees-using-sql-and-the-postgres-ltree-extension
    """
    MAX_LEVEL = 5  # Ограничение по ТЗ, но по желанию можно убрать и сделать бесконечное дерево

    name = models.CharField(max_length=255)
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="children",
    )

    level = models.PositiveIntegerField(default=1, editable=False)
    path = LTreeField(unique=True, editable=False)

    class Meta:
        indexes = [GistIndex(fields=["path"])]
        ordering = ["path"]
        verbose_name = "Отдел"
        verbose_name_plural = "Отделы"

    def clean(self):
        """Валидация уровня вложенности"""
        if self.parent_id:
            parent = Department.objects.only("level").get(pk=self.parent_id)
            if parent.level >= self.MAX_LEVEL:
                raise ValidationError(
                    f"Максимальная глубина иерархии - {self.MAX_LEVEL} уровней"
                )

    @transaction.atomic
    def save(self, *args, **kwargs):
        # Валидация перед сохранением
        self.full_clean()

        is_new = self.pk is None

        if is_new:
            super().save(*args, **kwargs)

        if self.parent_id:
            # Используем прямой SQL запрос для получения path из БД
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT path::text FROM employers_department WHERE id = %s",
                    [self.parent_id]
                )
                row = cursor.fetchone()
                parent_path_str = row[0] if row and row[0] else str(self.parent_id)

                cursor.execute(
                    "SELECT level FROM employers_department WHERE id = %s",
                    [self.parent_id]
                )
                row = cursor.fetchone()
                parent_level = row[0] if row else 0

            new_path = f"{parent_path_str}.{self.pk}"
            new_level = parent_level + 1
        else:
            new_path = str(self.pk)
            new_level = 1

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT path::text, level FROM employers_department WHERE id = %s",
                [self.pk]
            )
            row = cursor.fetchone()
            if row:
                current_path_str = row[0]
                current_level = row[1]
            else:
                current_path_str = None
                current_level = None

        if current_path_str != new_path or current_level != new_level:
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE employers_department SET path = %s::ltree, level = %s WHERE id = %s",
                    [new_path, new_level, self.pk]
                )

            self.path = new_path
            self.level = new_level

    def __str__(self) -> str:
        return self.name


class Employee(models.Model):
    full_name = models.CharField(max_length=255, db_index=True, verbose_name="ФИО")
    position = models.CharField(max_length=255, db_index=True, verbose_name="Должность")
    hired_at = models.DateField(db_index=True, verbose_name="Дата приема на работу")
    salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Зарплата"
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="employees",
        verbose_name="Подразделение"
    )

    # Денормализация для быстрых выборок по поддереву:
    structure_path = LTreeField(editable=False, db_index=True)

    class Meta:
        indexes = [GistIndex(fields=["structure_path"])]
        verbose_name = "Сотрудник"
        verbose_name_plural = "Сотрудники"
        ordering = ["full_name"]

    def save(self, *args, **kwargs):
        if self.department_id:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT path::text FROM employers_department WHERE id = %s",
                    [self.department_id]
                )
                row = cursor.fetchone()
                if row and row[0]:
                    self.structure_path = row[0]
                else:
                    self.structure_path = str(self.department_id)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.full_name
