import os
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

class UserMessage(BaseModel):
    message: str

# Load environment variables
load_dotenv()

# Initialize OpenAI client for using LLM service
client = OpenAI(
    base_url="https://api.studio.nebius.ai/v1/",
    api_key=os.environ.get("NEBIUS_API_KEY"),
)

# Track conversation states
conversation_states = {}

# List of questions to ask the user for optimal LLM responses
questions = [
    "Which artist(s) do you currently enjoy listening to? Could you name a few of your favorite tracks? What genres of music do you prefer? For example, pop, rock, jazz, or classical? Please give a maximum of 5 preferences for each of these. If you have no preferences, recommendations will be generated for you based on further instructions",
    "What's your current mood or activity? (e.g., relaxing, working out, studying, celebrating) Are you looking for upbeat, chill, or emotional tracks?",
    "How energetic should the music feel? (low energy for relaxation, high energy for workouts) Do you want tracks you can dance to, or should they be more laid-back?",
    "Do you prefer instrumental music, or would you like vocals to stand out?",
]

def get_next_question(current_responses):
    """
    Helper function for message.py to get the next question or process final response if final question has been asked
    """
    next_question_index = len(current_responses)
    
    if next_question_index < len(questions):
        return questions[next_question_index], False
    else:
        final_response = process_user_input_with_LLM(current_responses)
        return final_response, True

def process_user_input_with_LLM(user_responses):
    """
    Process all collected responses with LLM
    """
    user_preferences = " ".join(user_responses)
    refined_prompt = f'''
    Suggest music based on the following questions: {questions} and responses: {user_responses}. 
    Consider the semantic understanding captured by the embeddings derived from the user's preferences.
    Extract the user's preferences from the all the input text. Analyze: 
    
    1. Seed tracks: Exact names or IDs of songs. If not provided, use the text in the user_prompt to find recommendations. Limit to a max of 5.
    2. Seed artists: Names or IDs of artists. If not provided, use the text in the user_prompt to find recommendations. Limit to a max of 5.
    3. Seed genres: Relevant music genres. If not provided, use the text in the user_prompt to find recommendations. Limit to a max of 5.
    4. Optional features (if mentioned): The options are danceability, energy, tempo, and mood. Try to use as many of these as possible. Range is between 0 to 1.
    
    Input: {questions} and {user_preferences}
    Output: 1. Write a nuanced and deep description of what type of music is best for them, making sure you think in steps and provide reasoning as to why this type of music is best for the user. You may also give them a fun music personality type or analogy to classify them. Remember, this is supposed to be a personalized description and reasoning of the choices made, and not just regurgitated information from their responses. You need to experiment a little.
    2. Then return JSON format of information that is suitable for using with Music API to get recommendations.
    '''

    try:
        completion = client.chat.completions.create(
            model="meta-llama/Meta-Llama-3.1-405B-Instruct",
            messages=[{"role": "user", "content": refined_prompt}],
            temperature=0.8
        )
        return completion.choices[0].message.content
    except Exception as e:
        raise str(e)
    

def process_message(message: str):
    """
    Process a single message and return appropriate response
    """
    current_responses = conversation_states.get("responses", [])
    current_responses.append(message)
    conversation_states["responses"] = current_responses
    
    response, is_final = get_next_question(current_responses)
    
    if is_final:
        conversation_states.clear()  # Reset for next conversation
        
    return response, is_final


### CODE TO TEST THE LLM FUNCTION ONLY ###
def test_llm_conversation():
    """
    Test function to simulate a conversation with the LLM system
    """
    print("Starting test conversation...")
    
    # Simulate user responses to each question
    test_responses = [
        "I enjoy listening to The Weeknd, Drake, and Taylor Swift. I love R&B and Pop music.",
        "I'm currently studying and need something to help me focus.",
        "Low to medium energy would be perfect. More laid-back tracks.",
        "I prefer a mix of both instrumental and vocals, but nothing too distracting."
    ]
    
    for response in test_responses:
        print("\nUser input:", response)
        result, is_final = process_message(response)
        print("System response:", result)
        if is_final:
            print("\nFinal LLM Response:")
            print(result)

if __name__ == "__main__":
    test_llm_conversation()
