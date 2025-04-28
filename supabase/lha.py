import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://qjriwcvexqvqvtegeokv.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFqcml3Y3ZleHF2cXZ0ZWdlb2t2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQ3MTA3MjUsImV4cCI6MjA2MDI4NjcyNX0.qsAQ0DfTUwXBZb0BPLWa9XP1mqrhtkjzAxts_l9wyak")

# Initialize Supabase client
supabase= create_client(SUPABASE_URL, SUPABASE_KEY)

response=supabase.table("time_tracking")  .select("*").execute()

df=pd.DataFrame(response.data)

x=df.drop([],axis=1)
y=df[""]

x_train,x_test,y_train,y_test=train_test_split(x,y,test_size=0.2,random_state=42)

model=LinearRegression()
model.fit(x_train,y_train)

y_pred=model.predict(x_test)
