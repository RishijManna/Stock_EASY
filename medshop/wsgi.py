import os
import pathlib
from django.core.wsgi import get_wsgi_application

# Ensure MEDIA_ROOT exists at runtime (safe no-op on read-only)
media_root = os.getenv("MEDIA_ROOT")
if media_root:
    try:
        pathlib.Path(media_root).mkdir(parents=True, exist_ok=True)
    except Exception:
        # Ignore if the FS is read-only during runtime or container restart
        pass

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "medshop.settings")
application = get_wsgi_application()
