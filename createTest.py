import json
import sqlite3
import os
from datetime import datetime

class User:
    def __init__(self, hobbies, date_of_birth, dietary_restrictions=None,
                 disabilities=None, travel_dates=None, budget=None, current_location=None):
        self.hobbies = hobbies
        self.date_of_birth = date_of_birth
        self.dietary_restrictions = dietary_restrictions
        self.disabilities = disabilities
        self.travel_dates = travel_dates
        self.current_location = current_location
        self.budget = budget

def fetch_hobbies_from_db(hobby_list):
    conn = sqlite3.connect('hobbies.db')
    cursor = conn.cursor()
    hobbies = {}
    missing_hobbies = []

    for hobby in hobby_list:
        cursor.execute("SELECT l.location FROM hobbies h JOIN locations l ON h.id = l.hobby_id WHERE h.name = ?", (hobby,))
        locations = cursor.fetchall()
        if locations:
            hobbies[hobby] = ", ".join([loc[0] for loc in locations])
        else:
            missing_hobbies.append(hobby)

    conn.close()
    if missing_hobbies:
        print(f"The following hobbies do not exist in the database: {', '.join(missing_hobbies)}")
        return None
    return hobbies

def validate_dietary_restrictions_and_disabilities(dietary_restrictions, disabilities):
    valid_dietary_restrictions = [
        "None", "Halal", "Kosher", "Vegan", "Vegetarian", "Nut allergy", "Gluten-free",
        "Dairy-free", "Lactose intolerant", "Shellfish allergy", "Soy allergy", 
        "Egg allergy", "Seafood allergy", "Low-sodium", "Low-carb", "Low-fat", 
        "Diabetic", "No pork", "Pescatarian", "Paleo", "Keto", "FODMAP", 
        "Organic only", "Peanut allergy", "Citrus allergy", "Sulfite allergy", 
        "Fructose intolerance", "MSG sensitivity", "Raw food diet", 
        "Nightshade allergy"
    ]

    valid_disabilities = [
        "None", "Wheelchair user", "Visual impairment", "Hearing impairment", 
        "Cognitive disability", "Autism", "Dyslexia", "ADHD", 
        "Mobility impairment", "Chronic pain", "Mental health condition", 
        "Speech impairment", "Chronic illness", "Epilepsy", "Alzheimer's disease", 
        "Parkinson's disease", "Down syndrome", "Spinal cord injury", 
        "Cerebral palsy", "Muscular dystrophy", "Multiple sclerosis"
    ]

    invalid_dietary = [restriction for restriction in dietary_restrictions if restriction not in valid_dietary_restrictions]
    invalid_disabilities = [disability for disability in disabilities if disability not in valid_disabilities]

    if invalid_dietary:
        print(f"Invalid dietary restrictions: {', '.join(invalid_dietary)}. Please provide valid dietary restrictions.")
        return False
    if invalid_disabilities:
        print(f"Invalid disabilities: {', '.join(invalid_disabilities)}. Please provide valid disabilities.")
        return False

    return True

def generate_prompt(user):
    clause = []
    if user.date_of_birth == datetime.now().strftime("%d/%m/%Y"):  # Updated format to "dd/mm/yyyy"
        clause.append("It's the user's birthday today, so add an appropriate birthday venue activity.")

    if user.dietary_restrictions:
        clause.append(
            f"The user has dietary restrictions: {', '.join(user.dietary_restrictions)}. Recommend only places that meet these criteria for food and activities."
        )

    if user.disabilities:
        clause.append(
            f"The user has disabilities: {', '.join(user.disabilities)}. Ensure that recommended places are accessible."
        )

    if user.budget:
        clause.append(f"The user has a budget of {user.budget} KRW. Make sure the total costs of activities shown do not go above this.")

    clause.append("Only recommend places in South Korea.")

    hobbies_str = "; ".join([f"{hobby}: {details}" for hobby, details in user.hobbies.items()])
    prompt = (
        f"User Information:"
        f" - Hobbies: {hobbies_str}"
        f" - Dietary Restrictions: {', '.join(user.dietary_restrictions) if user.dietary_restrictions else 'None'}"
        f" - Disabilities: {', '.join(user.disabilities) if user.disabilities else 'None'}\n"
        f" Travel Information:"
        f" - Current Location: {user.current_location}, South Korea"
        f" - Travel Dates: {user.travel_dates[0]} to {user.travel_dates[1]}"
        f" - Budget: {user.budget} KRW"
        f" Request:"
        f" Recommend a minimum of 10 places for the user near {user.current_location} to visit."
        f" Consider the user's hobbies and recent headlines or trends from the internet related to the area, ensure recommendations are age-appropriate to the user's age."
        f"{' '.join(clause)}"
    )
    return prompt

def create_prompts_for_multiple_users(user_profiles, completions):
    generated_data = []
    for idx, profile in enumerate(user_profiles):
        if not isinstance(profile, dict):
            print(f"Expected a dictionary but got {type(profile)}. Skipping invalid entry.")
            continue

        user = User(
            hobbies=fetch_hobbies_from_db(profile.get('hobbies', [])),  # Fetch hobbies safely with .get() method
            date_of_birth=profile.get('date_of_birth', ''),  # Safely fetch date_of_birth
            dietary_restrictions=profile.get('dietary_restrictions', []),
            disabilities=profile.get('disabilities', []),
            travel_dates=profile.get('travel_dates', (None, None)),  # Ensure travel_dates defaults to a tuple
            current_location=profile.get('current_location', ''),
            budget=profile.get('budget', 0)
        )

        if validate_dietary_restrictions_and_disabilities(user.dietary_restrictions, user.disabilities):
            if user.hobbies:
                prompt_text = generate_prompt(user)
                completion_text = completions[idx] if idx < len(completions) else ""  # Ensure there's a matching completion or fallback to an empty string
                generated_data.append({
                    "prompt": prompt_text,
                    "completion": completion_text,
                    "split": "test"  # Include the 'split' field for all entries, test on train dipending
                })
            else:
                print("User hobbies validation failed.")
        else:
            print("Validation of dietary restrictions or disabilities failed.")
    
    return generated_data

    
    return generated_data

# Function to read and split the content from the text file
def split_entries(file_path):
    def clean_content(content):
        return content.replace('**', '').replace('\n', ' ').replace('\u2019', "'").replace('\u00e9', "e")

    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # Split the content based on "£" to separate sections
    entries = content.split('£')
    entries = [clean_content(entry.strip()) for entry in entries if entry.strip()]
    return entries

def write_prompts_to_jsonl(generated_data, jsonl_file_name='testDataForAITravelApp.jsonl'):
    with open(jsonl_file_name, 'w') as jsonlfile:
        for row in generated_data:
            jsonlfile.write(json.dumps(row) + '\n')
    


# Main Execution
if __name__ == "__main__":
    user_profiles = [
    {
        "hobbies": ["Cycling", "Photography", "Yoga", "Traveling", "Music"],#
        "date_of_birth": "12/05/1998",
        "dietary_restrictions": ["Halal"],
        "disabilities": ["None"],
        "travel_dates": ["02/09/2024", "08/09/2024"],
        "current_location": "Lotte Hotel Seoul",
        "budget": 1200000
    },
    {
        "hobbies": ["Art", "Cooking", "Yoga", "Reading", "Traveling"],#
        "date_of_birth": "07/09/2000",
        "dietary_restrictions": ["Vegan"],
        "disabilities": ["None"],
        "travel_dates": ["01/09/2024", "06/09/2024"],
        "current_location": "Signiel Busan",
        "budget": 1250000
    },
    {
        "hobbies": ["Fishing", "Photography", "Gardening", "Traveling", "Cycling"],#
        "date_of_birth": "14/03/1999",
        "dietary_restrictions": ["Kosher"],
        "disabilities": ["None"],
        "travel_dates": ["05/09/2024", "10/09/2024"],
        "current_location": "Grand Hyatt Incheon",
        "budget": 750000
    },
    ]
    
    # Read and process completions from the text file
    file_path = "testingData.txt"
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Could not find the text file: {file_path}")

    completions = split_entries(file_path)

    # Ensure completions are passed correctly to the function
    generated_data = create_prompts_for_multiple_users(user_profiles, completions)
    
    # Save generated data to JSONL
    write_prompts_to_jsonl(generated_data)


