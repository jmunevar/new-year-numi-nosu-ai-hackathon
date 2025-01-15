import os
import httpx  # Make sure to install httpx for making HTTP requests
from dotenv import load_dotenv
from openai import OpenAI
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
#from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

class UserMessage(BaseModel):
    message: str

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(
    base_url="https://api.studio.nebius.ai/v1/",
    api_key=os.environ.get("NEBIUS_API_KEY"),
)

# Initialize FastAPI
app = FastAPI(
    title="Music Recommendation API",
    description="API for getting personalized music recommendations"
)

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# List of questions to ask
questions = [
    "Which artist(s) do you currently enjoy listening to? Could you name a few of your favorite tracks? What genres of music do you prefer? For example, pop, rock, jazz, or classical? Please give a maximum of 5 preferences for each of these. If you have no preferences, recommendations will be generated for you based on further instructions",
    "What's your current mood or activity? (e.g., relaxing, working out, studying, celebrating) Are you looking for upbeat, chill, or emotional tracks?",
    "How energetic should the music feel? (low energy for relaxation, high energy for workouts) Do you want tracks you can dance to, or should they be more laid-back?",
    "Do you prefer instrumental music, or would you like vocals to stand out?",
]

# Store conversation state (in memory for this example)
conversation_states = {}

# Test endpoint to verify API is working
@app.post("/get-next-question")
async def get_next_question(user_message: UserMessage = None):
    """
    Get the next question or process final response.
    If user_message is None, return the first question.
    """
    if not user_message or not user_message.message:
        # First interaction - return first question
        return {"question": questions[0], "is_final": False}

    # Process the user's message and determine which question to send next
    current_responses = conversation_states.get("responses", [])
    current_responses.append(user_message.message)
    conversation_states["responses"] = current_responses
    
    next_question_index = len(current_responses)
    
    if next_question_index < len(questions):
        # Still have questions to ask
        return {
            "question": questions[next_question_index],
            "is_final": False
        }
    else:
        # All questions answered, generate final response
        final_response = process_user_input_with_LLM(current_responses)
        conversation_states.clear()  # Reset for next conversation
        return {
            "response": final_response,
            "is_final": True
        }

# def get_embeddings(text):
#     response = client.embeddings.create(
#         model="BAAI/bge-en-icl",
#         input=text,
#         encoding_format="float"
#     )
#     return response.data[0].embedding

# def combine_user_preferences(user_preferences):
#     """
#     Combines all user preferences into a single string for embedding
#     """
#     return " ".join(user_preferences.values())

# Create function to get suggestions for music from AI 
def process_user_input_with_LLM(user_responses):
    """Process all collected responses with LLM"""
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
        raise HTTPException(status_code=500, detail=str(e))
    
# # Placeholder Beethoven API integration
# def fetch_music_from_beethoven(music_type):
#     """
#     Fetch music from Beethoven API based on the music type.
#     This is a placeholder. Replace it with actual API calls to Beethoven.
#     """
#     # Simulate a response from Beethoven API
#     return f"https://beethoven.ai/music/{music_type.replace(' ', '_')}.mp3"

def interactive_session():
    """
    Multi-turn interactive session to refine user preferences.
    """
    print("Welcome to your personalized music recommender bot!")
    user_preferences = {}
    questions = [
        "Which artist(s) do you currently enjoy listening to? Could you name a few of your favorite tracks? What genres of music do you prefer? For example, pop, rock, jazz, or classical? Please give a maximum of 5 preferences for each of these. If you have no preferences, recommendations will be generated for you based on further instructions",
        "What’s your current mood or activity? (e.g., relaxing, working out, studying, celebrating) Are you looking for upbeat, chill, or emotional tracks?",
        "How energetic should the music feel? (low energy for relaxation, high energy for workouts) Do you want tracks you can dance to, or should they be more laid-back?",
        "Do you prefer instrumental music, or would you like vocals to stand out?",
    ]

    for question in questions:
        response = input(question + " User: ")
        if response.strip():
            user_preferences[question] = response.strip()

    # Generate embeddings from combined user preferences 
    user_preferences = " ".join(user_preferences.values())
    #preference_embeddings = get_embeddings(user_preferences)

    # Generate AI suggestion based on user preferences
    refined_prompt = (
        f'''
        Suggest music based on the following questions: {questions} and embeddings: {user_preferences}. 
        Extract the user's preferences from the all the input text. Analyze: 
        1. Seed tracks: Exact names or IDs of songs. If not provided, use the text in the user_prompt to find recommendations. Limit to a max of 5.
        2. Seed artists: Names or IDs of artists. If not provided, use the text in the user_prompt to find recommendations. Limit to a max of 5.
        3. Seed genres: Relevant music genres. If not provided, use the text in the user_prompt to find recommendations. Limit to a max of 5.
        4. Optional features (if mentioned): The options are danceability, energy, tempo, and mood. Try to use as many of these as possible. Range is between 0 to 1.
        
        Input: {questions} and {user_preferences}
        Output: 1. Write a nuanced and deep description of what type of music is best for them, making sure you think in steps and provide reasoning as to why this type of music is best for the user. You may also give thme a fun music personality type or analogy to classify them. Remember, this is supposed to be a personalized description and reasoning of the choices made, and not just regurgiated information from their responses. You need to experiment a litle.
        2. Then return JSON format of information that is suitable for using with Music API to get recommendations.
    
        "Please consider genres, moods, and specific activities."
        '''
        )
    
    print(
        f"\nGot it! Based on your preferences:\n{process_user_input_with_LLM(refined_prompt)}\n"
        #f"Here's music file from Beethoven that meets your needs:\n{music_file}\n"
        "Feel free to suggest any more details or changes!"
    )

@app.post("/process-answer")
async def process_answer(user_message: UserMessage):
    """
    Process each answer and determine if we need the next question or final LLM response.
    Works with the existing backend message structure.
    """
    # Get or initialize conversation state
    current_responses = conversation_states.get("responses", [])
    current_responses.append(user_message.message)
    conversation_states["responses"] = current_responses
    
    current_question_index = len(current_responses)
    
    # If we haven't asked all questions yet
    if current_question_index < len(questions):
        return {
            "message": questions[current_question_index],
            "isQuestion": True,
            "questionNumber": current_question_index + 1
        }
    
    # If we have all answers, process with LLM
    try:
        llm_response = process_user_input_with_LLM(current_responses)
        # Clear conversation state after successful processing
        conversation_states.clear()
        return {
            "message": llm_response,
            "isQuestion": False,
            "isFinal": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get-first-question")
async def get_first_question():
    """
    Return the first question to start the conversation
    """
    conversation_states.clear()  # Reset state for new conversation
    return {
        "message": questions[0],
        "isQuestion": True,
        "questionNumber": 1
    }

if __name__ == "__main__":
    interactive_session()