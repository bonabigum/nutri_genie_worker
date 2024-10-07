import pandas as pd
from model import recommend, output_recommended_recipes, calculate_nutrition_needs
from main import UserInfo, PredictionIn, params
import json
import requests

dataset = pd.read_json('recipes.json')
dataset['RecipeIngredientParts'] = dataset['RecipeIngredientParts'].apply(lambda x: ', '.join(x))
age1 = None
gender1=None
height1 = None
weight1 = None
health_goal1 = None
allergies1 =[]
def get_allergy_items(allergy_names):
    with open('allergens.json') as f:
        allergens_data = json.load(f)
    allergy_items = []
    for allergy_name in allergy_names:
        if allergy_name != '':
            allergy_items.append(allergy_name)
            for category in allergens_data['allergyCategories']:
                if category['name'].lower() == allergy_name.lower():
                    allergy_items.extend(category['items'])
                    break 
    return allergy_items
def test_get_user_id():
    try:
        response = requests.get('https://nutri-genie.onrender.com/get-user-id')
        response.raise_for_status()
        if response.status_code == 200:
            data = response.json()
            global age1, gender1, height1, weight1, health_goal1, allergies1
            age1 = data['user_info']['age'] #setting variables into its values
            gender1 = data['user_info']['gender']
            height1 = data['user_info']['height']
            weight1 = data['latest_weight_progress']
            health_goal1 = data['user_info']['health_goal']
            allergy_names = data['allergy_names']
            allergies1 = get_allergy_items(allergy_names)
        else:
            print(f"Error: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
test_get_user_id()
# sample user
user_info = UserInfo(
    age=age1,
    height=height1,
    weight=weight1,
    gender=gender1,
    health_goal=health_goal1
)
#print(user_info.__dict__)

prediction_input = PredictionIn( #prediction input
    user_info=user_info,
    #allergies=['chicken'],
    allergies = allergies1[:],
    params=params(n_neighbors=1, return_distance=False) # gives how many recipes to recommend
)


# calculate nutrition needs
nutrition_input = calculate_nutrition_needs(prediction_input.user_info)
# get recommendations
recommendation_dataframe = recommend(
    dataset,
    nutrition_input,
    prediction_input.ingredients,
    prediction_input.allergies,
    prediction_input.params.dict()
)
output = output_recommended_recipes(recommendation_dataframe)

#gets the price from json
with open('../Data/price.json') as f:
    price = json.load(f)
price_dict = {} #{(name, quantity):(price,unit)}

#serving size
api_url = 'https://api.calorieninjas.com/v1/nutrition?query='
api_key = 'uMh6rmANkTCIf6jkEmnUqw==5SplnfND1rVcKIa7'

# print the results
recommendations = []
if output is None:
    #print("No recommendations found.")
    recommendations.append('No recommendations found.')
else:
    for i, recipe in enumerate(output, 1):
        recipe_ingredients = recipe['RecipeIngredientParts'].split(', ')
        ingredients = [f"{qty} {part}" for qty, part in zip(recipe['Quantities'], recipe_ingredients)]
        ingredients_str = ', '.join(ingredients)
        recipe_instructions_str = ''.join(recipe['RecipeInstructions']).strip('[]')

        '''query = ', '.join(ingredients)
        response = requests.get(api_url + query, headers={'X-Api-Key': api_key})
        if response.status_code == requests.codes.ok:
            data = response.json()
            total_serving_size = sum(item['serving_size_g'] for item in data['items'])
            serving_size_str = f'{total_serving_size:.2f}g'
        else:
            serving_size_str = "Serving size computation not found"'''
        priced_ingredients = []
        for ingredient, quantity in zip(recipe_ingredients, recipe['Quantities']):
            found = False
            for item in price:
                if ingredient.lower() in item['Name'].lower():
                    priced_ingredients.append(f"{ingredient}: {item['Price']} Pesos per {item['Unit']}")
                    found = True
                    break
        if priced_ingredients:
            priced_ingredients_str = ', '.join(priced_ingredients)
        else:
            priced_ingredients_str = "No prices found."

        recipe_details = [ #for list
            i,
            recipe['Name'],
            recipe['Calories'],
            recipe['FatContent'],
            recipe['SaturatedFatContent'],
            recipe['CholesterolContent'],
            recipe['SodiumContent'],
            recipe['CarbohydrateContent'],
            recipe['FiberContent'],
            recipe['SugarContent'],
            recipe['ProteinContent'],
            recipe['Image'],
            ingredients_str,
            recipe_instructions_str,
            #serving_size_str,
            priced_ingredients_str
        ]
        recommendations.append(recipe_details)
print(recommendations)
with open('recommendations.json', 'w') as f:
    f.truncate(0)  #clears file
    json.dump(recommendations, f)
'''def get_recommendations():
    return recommendations
print(recommendations)'''
#python test_model.py to test
