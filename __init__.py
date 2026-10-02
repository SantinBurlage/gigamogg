"""GIGAMOGG — локальная нейросеть-собеседник с нитями, памятью и самообучением."""

import sys as _sys

# Консоль Windows по умолчанию в cp1252/cp866 и падает на русском тексте.
# Переводим вывод в UTF-8, чтобы кириллица в логах не ломала программу.
for _stream in (_sys.stdout, _sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

__version__ = "1.0.0"