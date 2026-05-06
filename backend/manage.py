import os
import sys
from pathlib import Path

# Add backend/ and packages/ to sys.path BEFORE anything else
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(backend_dir.parent / 'packages'))

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ram_admin.settings')
    import django
    django.setup()
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
