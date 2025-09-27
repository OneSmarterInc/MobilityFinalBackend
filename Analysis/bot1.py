import sqlite3
import pandas as pd
import google.generativeai as genai
from decouple import config
import json
import re

class Bot:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)