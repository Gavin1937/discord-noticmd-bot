
import time
from datetime import datetime


def get_timestr() -> str:
    return datetime.now().strftime("%H:%M:%S")