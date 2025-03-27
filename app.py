from flask import Flask, render_template, request, redirect, url_for, flash, session
import os
import json
import uuid
from datetime import datetime
import markdown

app = Flask(__name__)