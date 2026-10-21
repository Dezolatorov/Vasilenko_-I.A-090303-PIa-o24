"""Корневой пакет исходников проекта."""

import os
import sys

# Гарантируем, что src/ доступен в sys.path для импортов вида src.library.*
_SRC = os.path.dirname(os.path.abspath(__file__))
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)