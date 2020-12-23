from django.db import migrations

PROJECT_NAMES = ('User', 'Utils')
OPERATOR_NAMES = ('John', 'Jane')


def populate_projects_and_operators(apps, schema_editor):
    Project = apps.get_model('test_project', 'project')
    Operator = apps.get_model('test_project', 'operator')

    for i, project in enumerate(PROJECT_NAMES):
        Operator.objects.create(
            first_name=OPERATOR_NAMES[i],
            last_name='Doe',
            project=Project.objects.create(name=project),
        )


def delete_projects_and_operators(apps, schema_editor):
    Project = apps.get_model('test_project', 'project')
    Operator = apps.get_model('test_project', 'operator')

    Operator.objects.filter(
        first_name__in=OPERATOR_NAMES, project__name__in=PROJECT_NAMES
    ).delete()
    Project.objects.filter(name__in=PROJECT_NAMES).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('test_project', '0002_add_key_id_project'),
    ]

    operations = [
        migrations.RunPython(
            populate_projects_and_operators, reverse_code=delete_projects_and_operators
        ),
    ]
