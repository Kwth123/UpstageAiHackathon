import requests
import json
import matplotlib.pyplot as plt
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

# Set up OpenAI client for the base model 
from openai import OpenAI
openai_client = OpenAI(
    api_key="",
    base_url="https://api.upstage.ai/v1/solar"
)

# Predibase API configuration for fine-tuned models
predibase_api_token = "" 
predibase_url = "https://serving.app.predibase.com/7ea6d0/deployments/v2/llms/solar-1-mini-chat-240612/generate"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {predibase_api_token}"
}

# File path to your uploaded .jsonl file
file_path = r'C:\UpstageAiHackathon\testingDataForAITravelAppTest.jsonl'

# Reading the .jsonl file to extract the prompts and ground truth
test_prompts = []
ground_truths = []
with open(file_path, 'r') as file:
    for line in file:
        data = json.loads(line)
        if 'prompt' in data and 'ground_truth' in data:
            test_prompts.append(data['prompt'])
            ground_truths.append(data['ground_truth'])

def generate_base_response(prompt):
    try:
        response = openai_client.Completion.create(
            model="solar-1-mini-chat",
            prompt=prompt,
            max_tokens=100
        )
        return response.choices[0].text.strip()
    except Exception as e:
        print(f"Error generating base response: {e}")
        return ""

def generate_finetuned_response(prompt):
    try:
        payload = {
            "inputs": prompt,
            "parameters": {
                "adapter_id": "",  # Fine-tuned adapter ID location
                "adapter_source": "pbase",
                "max_new_tokens": 1000,
                "temperature": 0.6
            }
        }
        response = requests.post(predibase_url, data=json.dumps(payload), headers=headers)
        return response.json().get('generated_text', '').strip()  # Return empty string if no response is found
    except Exception as e:
        print(f"Error generating fine-tuned response: {e}")
        return ""

# Function to calculate similarity between generated responses and ground truth
def calculate_similarity(response, ground_truth):
    if not response or not ground_truth:
        return 0.0  

    vectorizer = TfidfVectorizer().fit_transform([response, ground_truth])
    vectors = vectorizer.toarray()
    cosine_sim = cosine_similarity(vectors)
    return cosine_sim[0][1]  # Return the similarity score between the two texts

base_model_scores = []
fine_tuned_model_scores = []

# Evaluate the models on each test prompt
for i, prompt in enumerate(test_prompts[:3]):  # Only use the first 3 prompts for this demonstration since there are only 3
    base_response = generate_base_response(prompt)  
    fine_tuned_response = generate_finetuned_response(prompt) 

    ground_truth = ground_truths[i]

    base_score = calculate_similarity(base_response, ground_truth)
    fine_tuned_score = calculate_similarity(fine_tuned_response, ground_truth)

    base_model_scores.append(base_score)
    fine_tuned_model_scores.append(fine_tuned_score)

# Plotting the similarity scores (if there are valid scores)
if base_model_scores and fine_tuned_model_scores:
    x_labels = [f"Prompt {i+1}" for i in range(len(base_model_scores))]
    x = range(len(base_model_scores))

    plt.figure(figsize=(10, 6))
    plt.plot(x, base_model_scores, label='Base Model (Solar)', marker='o', color='steelblue')
    plt.plot(x, fine_tuned_model_scores, label='Fine-Tuned Model (Predibase)', marker='o', color='orange')

    plt.xlabel('Test Prompts')
    plt.ylabel('Similarity Score (Cosine)')
    plt.title('Similarity Comparison: Base vs Fine-Tuned Model', fontsize=16, pad=20)
    plt.xticks(x, x_labels)
    plt.ylim([0, 1]) 
    plt.legend(fontsize=12)
    plt.tight_layout()
    plt.show()

# Stacked Bar Chart for Win Scores & Win Rates (mocked data)
base_win_score = 48
fine_tuned_win_score = 38
total_score = base_win_score + fine_tuned_win_score

base_win_rate = 5
fine_tuned_win_rate = 0
total_rate = base_win_rate + fine_tuned_win_rate


base_score_percentage = (base_win_score / total_score) * 100
fine_tuned_score_percentage = (fine_tuned_win_score / total_score) * 100

base_rate_percentage = (base_win_rate / total_rate) * 100
fine_tuned_rate_percentage = (fine_tuned_win_rate / total_rate) * 100

fig, ax = plt.subplots(figsize=(12, 8))

# Win score bar
ax.barh('Win score', base_score_percentage, color='steelblue', label=f'Base {base_win_score} ({int(base_score_percentage)}%)')
ax.barh('Win score', fine_tuned_score_percentage, left=base_score_percentage, color='orange', label=f'Fine-tuned {fine_tuned_win_score} ({int(fine_tuned_score_percentage)}%)')

# Win rate bar
ax.barh('Win rate', base_rate_percentage, color='steelblue')
ax.barh('Win rate', fine_tuned_rate_percentage, left=base_rate_percentage, color='orange')

ax.text(base_score_percentage / 2, 0, f'Base {base_win_score} ({int(base_score_percentage)}%)', va='center', ha='center', fontsize=12, color='white', weight='bold')
ax.text(base_score_percentage + fine_tuned_score_percentage / 2, 0, f'Fine-tuned {fine_tuned_win_score} ({int(fine_tuned_score_percentage)}%)', va='center', ha='center', fontsize=12, color='white', weight='bold')

ax.text(base_rate_percentage / 2, 1, f'Base {base_win_rate} ({int(base_rate_percentage)}%)', va='center', ha='center', fontsize=12, color='white', weight='bold')
ax.text(base_rate_percentage + fine_tuned_rate_percentage / 2, 1, f'Fine-tuned {fine_tuned_win_rate} ({int(fine_tuned_rate_percentage)}%)', va='center', ha='center', fontsize=12, color='white', weight='bold')

ax.set_xlabel('Percentage', fontsize=14)
ax.set_title('Base VS Fine-tuned Win Score & Rate', fontsize=16, pad=20)
ax.legend(loc='upper right', fontsize=12)

plt.tight_layout()
plt.show()
