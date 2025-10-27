"""Make cpf non-nullable for User.

This migration was created manually to avoid interactive prompts when
running makemigrations inside non-interactive containers. It alters
the `cpf` field to be `null=False, blank=False` and keeps the unique
constraint.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("gestao_usuarios_service", "0002_remove_user_users_role_0ace22_idx_remove_user_role_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='cpf',
            field=models.CharField(
                max_length=11,
                unique=True,
                null=False,
                blank=False,
                help_text="CPF obrigatório para todos os usuários",
            ),
        ),
    ]
