"""
Модуль для объединения лифтов и лестниц одного корпуса в единую сеть.
Каждый объект получает список ID связанных объектов.
"""

from .manager import NetworkManager
from .window import open_network_window

__all__ = ['NetworkManager', 'open_network_window']
