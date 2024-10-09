import numpy as np
import re
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer

#FOOR MAIN RECIPE
def scaling(dataframe):
    numerical_cols = dataframe.select_dtypes(include=['int64', 'float64']).columns
    scaler = StandardScaler()
    #prep_data = scaler.fit_transform(dataframe[numerical_cols])
    prep_data = scaler.fit_transform(dataframe[numerical_cols].values)
    return prep_data, scaler

def nn_predictor(prep_data): #predicting the nearest neighbors
    neigh = NearestNeighbors(metric='cosine',algorithm='brute')
    neigh.fit(prep_data)
    return neigh

def build_pipeline(neigh,scaler,params): #building the pipeline for the main recipe #THIS IS WITHOUT MAXIMUM NEIGHBORS
    transformer = FunctionTransformer(neigh.kneighbors,kw_args=params)
    pipeline=Pipeline([('std_scaler',scaler),('NN',transformer)])
    return pipeline

def extract_data(dataframe, ingredients, allergies): #extracting the data for the main recipe
    extracted_data = dataframe.copy()
    extracted_data = extract_ingredient_filtered_data(extracted_data, ingredients)
    extracted_data = filter_out_allergies(extracted_data, allergies)
    return extracted_data

def filter_out_allergies(dataframe, allergies): #filtering out the allergies
    if not allergies:
        return dataframe
    allergy_pattern = '|'.join(allergies)
    return dataframe[~dataframe['RecipeIngredientParts'].str.contains(allergy_pattern, case=False, regex=True)]

def extract_ingredient_filtered_data(dataframe, ingredients):
    extracted_data=dataframe.copy()
    regex_string='|'.join(map(lambda x:f'(?=.*{x})',ingredients))
    extracted_data=extracted_data[extracted_data['RecipeIngredientParts'].apply(lambda x: any(re.search(regex_string, ingredient, re.IGNORECASE) for ingredient in x))]
    return extracted_data

def apply_pipeline(pipeline,_input,extracted_data): #applying the pipeline for the main recipe
    _input=np.array(_input).reshape(1,-1)
    return extracted_data.iloc[pipeline.transform(_input)[0]]

def recommend(dataframe,_input,ingredients=[], allergies=[], params={'n_neighbors':3, 'return_distance':False}):
    extracted_data = extract_data(dataframe, ingredients, allergies)
    if extracted_data.shape[0] >= params['n_neighbors']:
        numerical_cols = extracted_data.select_dtypes(include=['int64', 'float64']).columns
        prep_data, scaler = scaling(extracted_data[numerical_cols])
        neigh = nn_predictor(prep_data)
        pipeline = build_pipeline(neigh, scaler, params)
        output = extracted_data.sample(n=3)
        return output.sample(n=3, replace=False)
    else:
        return None

def extract_quoted_strings(s):
    # Convert non-string values to strings
    if not isinstance(s, str):
        s = str(s)
    # Find all the strings inside double quotes
    strings = re.findall(r'"([^"]*)"', s)
    return strings

def output_recommended_recipes(dataframe):
    if dataframe is not None:
        output = dataframe.copy()
        output['RecipeInstructions'] = output['RecipeInstructions'].astype(str)
        output = output.to_dict("records")
        for recipe in output:
            #recipe['RecipeIngredientParts'] = extract_quoted_strings(recipe['RecipeIngredientParts'])
            #recipe['RecipeInstructions'] = extract_quoted_strings(recipe['RecipeInstructions'])
            recipe['Image'] = recipe.get('Image', None)
            # recipe['FatContent'] = recipe.get('FatContent', None)
    else:
        output = None
    return output

def calculate_nutrition_needs(user_info):
    bmr = 0
    if user_info.gender.lower() == 'male':
        bmr = 88.362 + (13.397 * user_info.weight) + (4.799 * user_info.height) - (5.677 * user_info.age)
    else:
        bmr = 447.593 + (9.247 * user_info.weight) + (3.098 * user_info.height) - (4.330 * user_info.age)

    calories = bmr
    protein = (calories * 0.3) / 4
    fat = (calories * 0.3) / 9
    carbs = (calories * 0.4) / 4
    sodium = 2300
    fiber = 25
    sugar = 50

    if user_info.health_goal == 'weight_loss':
        calories = bmr - 500
    elif user_info.health_goal == 'gain_weight':
        calories = bmr + 500
    elif user_info.health_goal == 'maintain_weight':
        calories = bmr
    elif user_info.health_goal == 'high_protein_diet':
        protein_ratio = 0.4  # adjust protein ratio to 40%
        protein = (calories * protein_ratio) / 4
        fat = (calories * 0.2) / 9  # adjust fat ratio to 20%
        carbs = (calories * 0.4) / 4  # adjust carb ratio to 40%
    elif user_info.health_goal == 'low_sodium':
        sodium = 1500  # adjust sodium value to 1500mg
        potassium = 4700  # adjust potassium value to 4700mg (to balance sodium)
    elif user_info.health_goal == 'low_cholesterol':
        cholesterol = 300  # adjust cholesterol value to 300mg
    elif user_info.health_goal == 'high-fiber':
        fiber = 25  # adjust fiber value to 25g
    elif user_info.health_goal == 'low_sugar':
        sugar = 20  # adjust sugar value to 20g
    elif user_info.health_goal == 'low_fat':
        fat = (calories * 0.2) / 9  # adjust fat ratio to 20%
        carbs = (calories * 0.5) / 4
    elif user_info.health_goal == 'keto_diet':
        fat = (calories * 0.7) / 9  # adjust fat ratio to 70%
        protein = (calories * 0.2) / 4
        carbs = (calories * 0.1) / 4

    return [calories, fat, 10, sodium, 2300, carbs, fiber, sugar, protein]

#FOR PRICE
