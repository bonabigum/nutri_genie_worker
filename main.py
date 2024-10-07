from fastapi import FastAPI
from pydantic import BaseModel
from typing import List,Optional
from pydantic.types import conlist
import pandas as pd
from model import recommend,output_recommended_recipes,calculate_nutrition_needs #from model
from typing import Dict, Optional

dataset = pd.read_json('recipes.json')
dataset['RecipeIngredientParts'] = dataset['RecipeIngredientParts'].apply(lambda x: ', '.join(x))
 
app = FastAPI()

class UserInfo(BaseModel): #TESTING PURPOSES
    age: int
    height: float  # in cm
    weight: float  # in kg
    gender: str
    health_goal: str

class params(BaseModel): #defines parameters for the nearest neighbors algo
    n_neighbors:int=5
    return_distance:bool=False

class PredictionIn(BaseModel): #defines the input structure for predictions, including nutrition input and optional ingredients
    user_info: UserInfo #TESTING PURPOSES
    ingredients:list[str]=[]
    allergies:list[str]=[]
    params:Optional[params]

class Recipe(BaseModel): #structure of recipe and nutritional info
    Name:str
    RecipeIngredientParts:list[str]
    Quantities:list[str]
    Calories:float
    FatContent:float
    SaturatedFatContent:float
    CholesterolContent:float
    SodiumContent:float
    CarbohydrateContent:float
    FiberContent:float
    SugarContent:float
    ProteinContent:float
    RecipeInstructions:list[str]
    Image: str

class PredictionOut(BaseModel): #output structure of recipe objs
    output: Optional[List[Recipe]] = None

@app.get("/") #endpoint
def home():
    return {"health_check": "OK"}

@app.post("/predict/",response_model=PredictionOut) #from model.py
def update_item(prediction_input:PredictionIn):
    nutrition_input = calculate_nutrition_needs(prediction_input.user_info)
    print("Nutrition Input:", nutrition_input)
    recommendation_dataframe = recommend(
        dataset,
        nutrition_input,
        prediction_input.ingredients,
        prediction_input.allergies,
        prediction_input.params.dict()
    )
    output = output_recommended_recipes(recommendation_dataframe)
    if output is None:
        return {"output": None}
    else:
        return {"output": output}
