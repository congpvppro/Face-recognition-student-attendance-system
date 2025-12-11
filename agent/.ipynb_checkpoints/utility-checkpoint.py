# Importing
import os #For env
import re
from langchain_groq import ChatGroq
from langchain_community.utilities import SQLDatabase
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from datetime import datetime, time, date  
import pandas as pd
class EntryAgent:
    