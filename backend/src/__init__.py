from flask import Flask
app = Flask (__name__,
  static_url_path='', 
  static_folder='./view',
  template_folder='./view'
)

from . import routes