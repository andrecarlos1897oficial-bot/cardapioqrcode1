import os
import sys
from flask import Flask

# Adiciona o diretório do projeto ao path
project_home = '/home/seu-usuario/cardapio-qrcode'
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

from app import app as application

if __name__ == '__main__':
    application.run()
