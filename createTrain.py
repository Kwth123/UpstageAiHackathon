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
                    "split": "train"  # Include the 'split' field for all entries, test on train dipending 
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

def write_prompts_to_jsonl(generated_data, jsonl_file_name='trainingDataForAITravelApp.jsonl'):
    with open(jsonl_file_name, 'w') as jsonlfile:
        for row in generated_data:
            jsonlfile.write(json.dumps(row) + '\n')
    


# Main Execution
if __name__ == "__main__":
    user_profiles = [

        {"hobbies": ["Swimming", "Running", "Photography", "Yoga", "Traveling"], "date_of_birth": "12/05/1998", "dietary_restrictions": ["Halal"], "disabilities": ["None"], "travel_dates": ("02/09/2024", "08/09/2024"), "current_location": "Lotte Hotel Seoul", "budget": 1200000},
        {"hobbies": ["Art", "Cooking", "Yoga", "Reading", "Traveling"], "date_of_birth": "07/09/2000", "dietary_restrictions": ["Vegan"], "disabilities": ["None"], "travel_dates": ("10/10/2024", "15/10/2024"), "current_location": "Signiel Busan", "budget": 1250000},
        {"hobbies": ["Cycling", "Photography", "Gardening", "Reading", "Music"], "date_of_birth": "14/03/1999", "dietary_restrictions": ["Kosher"], "disabilities": ["None"], "travel_dates": ("15/09/2024", "20/09/2024"), "current_location": "Grand Hyatt Incheon", "budget": 750000},
        {"hobbies": ["Fishing", "Bird Watching", "Gardening", "Photography", "Traveling"], "date_of_birth": "19/06/1997", "dietary_restrictions": ["Gluten-free"], "disabilities": ["None"], "travel_dates": ("20/09/2024", "26/09/2024"), "current_location": "Jeju Shilla Hotel", "budget": 1440000},
        {"hobbies": ["Hiking", "Writing", "Art", "Photography", "Reading"], "date_of_birth": "23/02/2001", "dietary_restrictions": ["Dairy-free"], "disabilities": ["None"], "travel_dates": ("05/11/2024", "10/11/2024"), "current_location": "Daegu Grand Hotel", "budget": 700000},
        {"hobbies": ["Yoga", "Photography", "Reading", "Cooking", "Gardening"], "date_of_birth": "15/07/1996", "dietary_restrictions": ["Vegan", "Nut allergy"], "disabilities": ["Cognitive disability"], "travel_dates": ("03/09/2024", "10/09/2024"), "current_location": "Gwangju Utop Boutique Hotel & Residence", "budget": 1120000},
        {"hobbies": ["Rock Climbing", "Camping", "Yoga", "Gardening", "Photography"], "date_of_birth": "04/12/2002", "dietary_restrictions": ["Pescatarian"], "disabilities": ["Wheelchair user"], "travel_dates": ("18/09/2024", "24/09/2024"), "current_location": "Lotte City Hotel Daejeon", "budget": 900000},
        {"hobbies": ["Writing", "Art", "Photography", "Reading", "Cooking"], "date_of_birth": "28/04/2000", "dietary_restrictions": ["Halal"], "disabilities": ["Visual impairment"], "travel_dates": ("07/10/2024", "14/10/2024"), "current_location": "Ulsan Hyundai Hotel", "budget": 1120000},
        
        {"hobbies": ["Fitness", "Running", "Yoga", "Cooking", "Traveling"], "date_of_birth": "10/01/1995", "dietary_restrictions": ["Vegan", "Low-carb"], "disabilities": ["Hearing impairment"], "travel_dates": ("25/10/2024", "30/10/2024"), "current_location": "Suwon Novotel Ambassador", "budget": 1250000},
        {"hobbies": ["Photography", "Gardening", "Bird Watching", "Fishing", "Art"], "date_of_birth": "21/11/1998", "dietary_restrictions": ["Kosher", "Gluten-free"], "disabilities": ["None"], "travel_dates": ("12/09/2024", "18/09/2024"), "current_location": "Changwon Grand City Hotel", "budget": 960000},
        {"hobbies": ["Bird Watching", "Hiking", "Fishing", "Photography", "Gardening"], "date_of_birth": "29/08/2003", "dietary_restrictions": ["None"], "disabilities": ["Mental health condition"], "travel_dates": ("01/10/2024", "07/10/2024"), "current_location": "Jeju Sun Hotel & Casino", "budget": 840000},
        {"hobbies": ["Music", "Art", "History", "Photography", "Reading"], "date_of_birth": "18/02/1997", "dietary_restrictions": ["None"], "disabilities": ["Mobility impairment"], "travel_dates": ("05/09/2024", "12/09/2024"), "current_location": "Incheon Paradise City Hotel", "budget": 1680000},
        {"hobbies": ["Yoga", "Art", "Writing", "Gardening", "Fitness"], "date_of_birth": "10/10/2001", "dietary_restrictions": ["None"], "disabilities": ["Chronic pain"], "travel_dates": ("15/09/2024", "20/09/2024"), "current_location": "Busan The Westin Chosun Hotel", "budget": 1000000},
        {"hobbies": ["Cycling", "Hiking", "Reading", "Photography", "Traveling"], "date_of_birth": "17/05/1996", "dietary_restrictions": ["None"], "disabilities": ["Cognitive disability"], "travel_dates": ("25/09/2024", "30/09/2024"), "current_location": "Seoul Four Seasons Hotel", "budget": 1800000},
        {"hobbies": ["Cooking", "Writing", "Photography", "Gardening", "Art"], "date_of_birth": "14/07/1999", "dietary_restrictions": ["None"], "disabilities": ["ADHD"], "travel_dates": ("10/09/2024", "15/09/2024"), "current_location": "Gwangju Ramada Plaza", "budget": 800000},
        {"hobbies": ["Cycling", "Photography", "Traveling", "Writing", "Art"], "date_of_birth": "07/01/2000", "dietary_restrictions": ["None"], "disabilities": ["None"], "travel_dates": ("01/11/2024", "07/11/2024"), "current_location": "Lotte Hotel Jeju", "budget": 1500000},
        {"hobbies": ["Swimming", "Running", "Yoga", "Gardening", "Music"], "date_of_birth": "25/06/2002", "dietary_restrictions": ["None"], "disabilities": ["None"], "travel_dates": ("05/09/2024", "10/09/2024"), "current_location": "Novotel Ambassador Seoul Yongsan", "budget": 1200000},
        {"hobbies": ["Fishing", "Bird Watching", "Cycling", "Traveling", "Fitness"], "date_of_birth": "20/12/1998", "dietary_restrictions": ["None"], "disabilities": ["None"], "travel_dates": ("12/10/2024", "18/10/2024"), "current_location": "InterContinental Busan", "budget": 1440000},
        {"hobbies": ["Art", "History", "Writing", "Photography", "Yoga"], "date_of_birth": "02/03/2001", "dietary_restrictions": ["None"], "disabilities": ["None"], "travel_dates": ("10/09/2024", "16/09/2024"), "current_location": "Jeju Haevichi Hotel & Resort", "budget": 1260000},
        {"hobbies": ["Music", "Fitness", "Yoga", "Photography", "Traveling"], "date_of_birth": "29/04/1995", "dietary_restrictions": ["None"], "disabilities": ["None"], "travel_dates": ("15/09/2024", "21/09/2024"), "current_location": "Busan Paradise Hotel", "budget": 1500000},
        {"hobbies": ["Photography", "Cycling", "Traveling", "Writing", "Yoga"], "date_of_birth": "03/09/2002", "dietary_restrictions": ["None"], "disabilities": ["None"], "travel_dates": ("01/09/2024", "06/09/2024"), "current_location": "Lotte Hotel Jeju", "budget": 1260000},
        {"hobbies": ["Music", "Fitness", "Cycling", "Photography", "Art"], "date_of_birth": "22/10/1996", "dietary_restrictions": ["None"], "disabilities": ["None"], "travel_dates": ("20/10/2024", "26/10/2024"), "current_location": "Ramada Plaza Gwangju", "budget": 1440000},
        
        
        {"hobbies": ["Reading", "History", "Art", "Yoga", "Traveling"], "date_of_birth": "05/11/1999", "dietary_restrictions": ["None"], "disabilities": ["None"], "travel_dates": ("03/11/2024", "08/11/2024"), "current_location": "Jeonju Lahan Hotel", "budget": 1050000},
        {"hobbies": ["Cycling", "Photography", "Swimming", "Traveling", "Fitness"], "date_of_birth": "12/01/1998", "dietary_restrictions": ["None"], "disabilities": ["None"], "travel_dates": ("10/01/2024", "16/01/2024"), "current_location": "Seogwipo KAL Hotel", "budget": 1320000},
        {"hobbies": ["Bird Watching", "Fishing", "Gardening", "Photography", "Traveling"], "date_of_birth": "02/12/1997", "dietary_restrictions": ["None"], "disabilities": ["None"], "travel_dates": ("01/12/2024", "07/12/2024"), "current_location": "Pohang Ramada Encore Hotel", "budget": 1080000},
        {"hobbies": ["Hiking", "Art", "Reading", "Yoga", "Photography"], "date_of_birth": "14/09/2001", "dietary_restrictions": ["None"], "disabilities": ["None"], "travel_dates": ("13/09/2024", "18/09/2024"), "current_location": "Gangneung Seamarq Hotel", "budget": 1380000},
        {"hobbies": ["Swimming", "Dancing", "Music", "Yoga", "Reading"], "date_of_birth": "07/08/1995", "dietary_restrictions": ["None"], "disabilities": ["None"], "travel_dates": ("05/08/2024", "10/08/2024"), "current_location": "Andong Grand Hotel", "budget": 950000},
        {"hobbies": ["Fitness", "Art", "Cooking", "Photography", "Reading"], "date_of_birth": "18/04/2000", "dietary_restrictions": ["None"], "disabilities": ["None"], "travel_dates": ("16/04/2024", "22/04/2024"), "current_location": "Daegu Hotel Inter-Burgo", "budget": 1200000},
        {"hobbies": ["Writing", "Traveling", "Fitness", "Reading", "Gardening"], "date_of_birth": "11/07/1997", "dietary_restrictions": ["None"], "disabilities": ["None"], "travel_dates": ("10/07/2024", "15/07/2024"), "current_location": "Busan Marriott Hotel", "budget": 1150000},
        {"hobbies": ["Cycling", "Photography", "Gardening", "Music", "Art"], "date_of_birth": "24/05/2003", "dietary_restrictions": ["None"], "disabilities": ["None"], "travel_dates": ("22/05/2024", "28/05/2024"), "current_location": "Sokcho Kensington Hotel", "budget": 1320000},
        {"hobbies": ["Yoga", "Writing", "Reading", "Photography", "Traveling"], "date_of_birth": "15/03/2002", "dietary_restrictions": ["None"], "disabilities": ["None"], "travel_dates": ("14/03/2024", "20/03/2024"), "current_location": "Seoul Signiel Hotel", "budget": 2100000},
        {"hobbies": ["Cooking", "Fitness", "Dancing", "Music", "Photography"], "date_of_birth": "08/10/1998", "dietary_restrictions": ["None"], "disabilities": ["None"], "travel_dates": ("07/10/2024", "13/10/2024"), "current_location": "Busan The Westin Chosun", "budget": 1500000},
        {"hobbies": ["Rock Climbing", "Yoga", "Photography", "Traveling", "Fitness"], "date_of_birth": "01/06/1999", "dietary_restrictions": ["None"], "disabilities": ["None"], "travel_dates": ("31/05/2024", "06/06/2024"), "current_location": "Cheongju Grand Plaza Hotel", "budget": 1280000},
        {"hobbies": ["Hiking", "Writing", "Gardening", "Photography", "Traveling"], "date_of_birth": "21/12/1996", "dietary_restrictions": ["None"], "disabilities": ["None"], "travel_dates": ("20/12/2024", "26/12/2024"), "current_location": "Jeonju Best Western Hotel", "budget": 1340000},
        {"hobbies": ["Cycling", "Hiking", "Photography", "Art", "Music"], "date_of_birth": "09/09/2001", "dietary_restrictions": ["None"], "disabilities": ["None"], "travel_dates": ("08/09/2024", "14/09/2024"), "current_location": "Incheon Songdo Central Park Hotel", "budget": 1320000},
        {"hobbies": ["Fishing", "Bird Watching", "Cycling", "Photography", "Art"], "date_of_birth": "25/04/1995", "dietary_restrictions": ["None"], "disabilities": ["None"], "travel_dates": ("24/04/2024", "30/04/2024"), "current_location": "Gyeongju Hilton Hotel", "budget": 1480000},
        {"hobbies": ["Yoga", "Fitness", "Gardening", "Photography", "Music"], "date_of_birth": "12/11/1999", "dietary_restrictions": ["None"], "disabilities": ["None"], "travel_dates": ("11/11/2024", "17/11/2024"), "current_location": "Yeosu MVL Hotel", "budget": 1400000},
        {"hobbies": ["Reading", "Art", "Yoga", "Photography", "Traveling"], "date_of_birth": "02/02/2000", "dietary_restrictions": ["None"], "disabilities": ["None"], "travel_dates": ("01/02/2024", "06/02/2024"), "current_location": "Suwon Courtyard by Marriott", "budget": 1050000},
        {"hobbies": ["Fitness", "Cycling", "Photography", "Traveling", "Gardening"], "date_of_birth": "18/06/1997", "dietary_restrictions": ["None"], "disabilities": ["None"], "travel_dates": ("17/06/2024", "23/06/2024"), "current_location": "Daejeon LOTTE City Hotel", "budget": 1360000},
        {"hobbies": ["Swimming", "Photography", "Traveling", "Art", "Gardening"], "date_of_birth": "23/11/2003", "dietary_restrictions": ["None"], "disabilities": ["None"], "travel_dates": ("22/11/2024", "28/11/2024"), "current_location": "Ulsan Hyundai Hotel", "budget": 1440000}
        
    ]
    
    # Read and process completions from the text file
    file_path = "testingData.txt"  # Replace with the correct path 
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Could not find the text file: {file_path}")

    completions = split_entries(file_path)

    # Ensure completions are passed correctly to the function
    generated_data = create_prompts_for_multiple_users(user_profiles, completions)
    
    # Save generated data to JSONL
    write_prompts_to_jsonl(generated_data)



