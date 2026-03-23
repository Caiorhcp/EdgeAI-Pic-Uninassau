# conftest.py — configura sys.path para pytest encontrar o pacote src/
import sys
import os

# Adiciona a raiz do projeto ao sys.path para que imports como
# 'from src.domain...' funcionem corretamente nos testes
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
