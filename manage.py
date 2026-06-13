#!/usr/bin/env python
"""Punto de entrada de Django para tareas administrativas."""

import os
import sys


def main():
    """Ejecuta las tareas administrativas de Django."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "No se puede importar Django. Asegúrate de que está instalado y "
            "de que el entorno virtual está activo. Ejecuta: pip install -r requirements.txt"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
