import logging
import os


logger = logging.getLogger(__name__)
DEBUG = bool(os.environ.get('DEBUG', False))

