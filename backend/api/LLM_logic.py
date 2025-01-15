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
    "Hi there \U0001F600!! I'm here to help create your perfect playlist. I can suggest you Spotify Playlists with your favorite music, or help you create new AI music with beetoven.ai. Lets's get started! \n Which artist(s) do you currently enjoy listening to? \n Could you name a few of your favorite tracks? What genres of music do you prefer? For example, pop, rock, jazz, or classical? \n Please give a maximum of 5 preferences for each of these. If you have no preferences, I can either add some of my suggestions based on your instructions or work with your inputs",
    "What's your current mood or activity? (e.g., relaxing, working out, studying, celebrating) \n Are you looking for upbeat, chill, or emotional tracks?",
    "How energetic should the music feel? (low energy for relaxation, high energy for workouts) \n Do you want tracks you can dance to, or should they be more laid-back?",
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
    Suggest music based on the following questions: {questions} and responses: {user_responses} 
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
        llm_response = completion.choices[0].message.content
        # Get API-specific formats
        spotify_format =  create_API_Spotify(user_preferences)
        beetoven_format = create_API_beetoven(user_preferences)
        
        # Combine all responses
        combined_response = {
            "analysis": llm_response,
            "spotify_parameters": spotify_format,
            "beetoven_parameters": beetoven_format
        }

        return format_final_response(combined_response)
    except Exception as e:
        raise str(e)
    

def format_final_response(response: dict) -> str:
    """Format the final response into readable paragraphs"""
    formatted_response = (
        f"Analysis:\n{response['analysis']}\n\n"
        f"-------------------\n"
        f"Spotify Recommendations Parameters:\n{response['spotify_parameters']}\n\n"
        f"-------------------\n"
        f"Beetoven.ai Generation Parameters:\n{response['beetoven_parameters']}"
    )
    return formatted_response

def process_message(message: str):
    """
    Process a single message and return appropriate response
    """
    # Check if this is the first message (empty conversation)
    if not conversation_states.get("responses"):
        conversation_states["responses"] = []
        # Return the first question immediately
        return questions[0], False
    
    current_responses = conversation_states["responses"]
    current_responses.append(message)
    conversation_states["responses"] = current_responses
    
    response, is_final = get_next_question(current_responses)
    
    if is_final:
        conversation_states.clear()  # Reset for next conversation
        
    return response, is_final

SPOTIFY_API_FORMAT = f'''
        limit (datatype: integer)
        The target size of the list of recommended tracks. For seeds with unusually small pools or when highly restrictive filtering is applied, it may be impossible to generate the requested number of recommended tracks. Debugging information for such cases is available in the response. Default: 20. Minimum: 1. Maximum: 100.

        Default: limit=20
        Range: 1 - 100
        Example: limit=10

        market (datatype: string)
        An ISO 3166-1 alpha-2 country code. If a country code is specified, only content that is available in that market will be returned.
        If a valid user access token is specified in the request header, the country associated with the user account will take priority over this parameter.
        Note: If neither market or user country are provided, the content is considered unavailable for the client.
        Users can view the country that is associated with their account in the account settings.

        Example: market=ES
        seed_artists (datatype: string) (REQUIRED)
        A comma separated list of Spotify IDs for seed artists. Up to 5 seed values may be provided in any combination of seed_artists, seed_tracks and seed_genres.
        Note: only required if seed_genres and seed_tracks are not set.

        Example: seed_artists=4NHQUGzhtTLFvgF5SZesLK
        seed_genres (datatype: string) (REQUIRED)
        A comma separated list of any genres in the set of available genre seeds. Up to 5 seed values may be provided in any combination of seed_artists, seed_tracks and seed_genres.
        Note: only required if seed_artists and seed_tracks are not set.

        Example: seed_genres=classical,country
        seed_tracks (datatype: string) (REQUIRED)
        A comma separated list of Spotify IDs for a seed track. Up to 5 seed values may be provided in any combination of seed_artists, seed_tracks and seed_genres.
        Note: only required if seed_artists and seed_genres are not set.

        Example: seed_tracks=0c6xIDDpzE81m2q797ordA
        min_acousticness (datatype: number)
        For each tunable track attribute, a hard floor on the selected track attribute’s value can be provided. See tunable track attributes below for the list of available options. For example, min_tempo=140 would restrict results to only those tracks with a tempo of greater than 140 beats per minute.

        Range: 0 - 1
        max_acousticness
        number
        For each tunable track attribute, a hard ceiling on the selected track attribute’s value can be provided. See tunable track attributes below for the list of available options. For example, max_instrumentalness=0.35 would filter out most tracks that are likely to be instrumental.

        Range: 0 - 1
        target_acousticness
        number
        For each of the tunable track attributes (below) a target value may be provided. Tracks with the attribute values nearest to the target values will be preferred. For example, you might request target_energy=0.6 and target_danceability=0.8. All target values will be weighed equally in ranking results.

        Range: 0 - 1
        min_danceability
        number
        For each tunable track attribute, a hard floor on the selected track attribute’s value can be provided. See tunable track attributes below for the list of available options. For example, min_tempo=140 would restrict results to only those tracks with a tempo of greater than 140 beats per minute.

        Range: 0 - 1
        max_danceability
        number
        For each tunable track attribute, a hard ceiling on the selected track attribute’s value can be provided. See tunable track attributes below for the list of available options. For example, max_instrumentalness=0.35 would filter out most tracks that are likely to be instrumental.

        Range: 0 - 1
        target_danceability
        number
        For each of the tunable track attributes (below) a target value may be provided. Tracks with the attribute values nearest to the target values will be preferred. For example, you might request target_energy=0.6 and target_danceability=0.8. All target values will be weighed equally in ranking results.

        Range: 0 - 1
        min_duration_ms
        integer
        For each tunable track attribute, a hard floor on the selected track attribute’s value can be provided. See tunable track attributes below for the list of available options. For example, min_tempo=140 would restrict results to only those tracks with a tempo of greater than 140 beats per minute.

        max_duration_ms
        integer
        For each tunable track attribute, a hard ceiling on the selected track attribute’s value can be provided. See tunable track attributes below for the list of available options. For example, max_instrumentalness=0.35 would filter out most tracks that are likely to be instrumental.

        target_duration_ms
        integer
        Target duration of the track (ms)

        min_energy
        number
        For each tunable track attribute, a hard floor on the selected track attribute’s value can be provided. See tunable track attributes below for the list of available options. For example, min_tempo=140 would restrict results to only those tracks with a tempo of greater than 140 beats per minute.

        Range: 0 - 1
        max_energy
        number
        For each tunable track attribute, a hard ceiling on the selected track attribute’s value can be provided. See tunable track attributes below for the list of available options. For example, max_instrumentalness=0.35 would filter out most tracks that are likely to be instrumental.

        Range: 0 - 1
        target_energy
        number
        For each of the tunable track attributes (below) a target value may be provided. Tracks with the attribute values nearest to the target values will be preferred. For example, you might request target_energy=0.6 and target_danceability=0.8. All target values will be weighed equally in ranking results.

        Range: 0 - 1
        min_instrumentalness
        number
        For each tunable track attribute, a hard floor on the selected track attribute’s value can be provided. See tunable track attributes below for the list of available options. For example, min_tempo=140 would restrict results to only those tracks with a tempo of greater than 140 beats per minute.

        Range: 0 - 1
        max_instrumentalness
        number
        For each tunable track attribute, a hard ceiling on the selected track attribute’s value can be provided. See tunable track attributes below for the list of available options. For example, max_instrumentalness=0.35 would filter out most tracks that are likely to be instrumental.

        Range: 0 - 1
        target_instrumentalness
        number
        For each of the tunable track attributes (below) a target value may be provided. Tracks with the attribute values nearest to the target values will be preferred. For example, you might request target_energy=0.6 and target_danceability=0.8. All target values will be weighed equally in ranking results.

        Range: 0 - 1
        min_key
        integer
        For each tunable track attribute, a hard floor on the selected track attribute’s value can be provided. See tunable track attributes below for the list of available options. For example, min_tempo=140 would restrict results to only those tracks with a tempo of greater than 140 beats per minute.

        Range: 0 - 11
        max_key
        integer
        For each tunable track attribute, a hard ceiling on the selected track attribute’s value can be provided. See tunable track attributes below for the list of available options. For example, max_instrumentalness=0.35 would filter out most tracks that are likely to be instrumental.

        Range: 0 - 11
        target_key
        integer
        For each of the tunable track attributes (below) a target value may be provided. Tracks with the attribute values nearest to the target values will be preferred. For example, you might request target_energy=0.6 and target_danceability=0.8. All target values will be weighed equally in ranking results.

        Range: 0 - 11
        min_liveness
        number
        For each tunable track attribute, a hard floor on the selected track attribute’s value can be provided. See tunable track attributes below for the list of available options. For example, min_tempo=140 would restrict results to only those tracks with a tempo of greater than 140 beats per minute.

        Range: 0 - 1
        max_liveness
        number
        For each tunable track attribute, a hard ceiling on the selected track attribute’s value can be provided. See tunable track attributes below for the list of available options. For example, max_instrumentalness=0.35 would filter out most tracks that are likely to be instrumental.

        Range: 0 - 1
        target_liveness
        number
        For each of the tunable track attributes (below) a target value may be provided. Tracks with the attribute values nearest to the target values will be preferred. For example, you might request target_energy=0.6 and target_danceability=0.8. All target values will be weighed equally in ranking results.

        Range: 0 - 1
        min_loudness
        number
        For each tunable track attribute, a hard floor on the selected track attribute’s value can be provided. See tunable track attributes below for the list of available options. For example, min_tempo=140 would restrict results to only those tracks with a tempo of greater than 140 beats per minute.

        max_loudness
        number
        For each tunable track attribute, a hard ceiling on the selected track attribute’s value can be provided. See tunable track attributes below for the list of available options. For example, max_instrumentalness=0.35 would filter out most tracks that are likely to be instrumental.

        target_loudness
        number
        For each of the tunable track attributes (below) a target value may be provided. Tracks with the attribute values nearest to the target values will be preferred. For example, you might request target_energy=0.6 and target_danceability=0.8. All target values will be weighed equally in ranking results.

        min_mode
        integer
        For each tunable track attribute, a hard floor on the selected track attribute’s value can be provided. See tunable track attributes below for the list of available options. For example, min_tempo=140 would restrict results to only those tracks with a tempo of greater than 140 beats per minute.

        Range: 0 - 1
        max_mode
        integer
        For each tunable track attribute, a hard ceiling on the selected track attribute’s value can be provided. See tunable track attributes below for the list of available options. For example, max_instrumentalness=0.35 would filter out most tracks that are likely to be instrumental.

        Range: 0 - 1
        target_mode
        integer
        For each of the tunable track attributes (below) a target value may be provided. Tracks with the attribute values nearest to the target values will be preferred. For example, you might request target_energy=0.6 and target_danceability=0.8. All target values will be weighed equally in ranking results.

        Range: 0 - 1
        min_popularity
        integer
        For each tunable track attribute, a hard floor on the selected track attribute’s value can be provided. See tunable track attributes below for the list of available options. For example, min_tempo=140 would restrict results to only those tracks with a tempo of greater than 140 beats per minute.

        Range: 0 - 100
        max_popularity
        integer
        For each tunable track attribute, a hard ceiling on the selected track attribute’s value can be provided. See tunable track attributes below for the list of available options. For example, max_instrumentalness=0.35 would filter out most tracks that are likely to be instrumental.

        Range: 0 - 100
        target_popularity
        integer
        For each of the tunable track attributes (below) a target value may be provided. Tracks with the attribute values nearest to the target values will be preferred. For example, you might request target_energy=0.6 and target_danceability=0.8. All target values will be weighed equally in ranking results.

        Range: 0 - 100
        min_speechiness
        number
        For each tunable track attribute, a hard floor on the selected track attribute’s value can be provided. See tunable track attributes below for the list of available options. For example, min_tempo=140 would restrict results to only those tracks with a tempo of greater than 140 beats per minute.

        Range: 0 - 1
        max_speechiness
        number
        For each tunable track attribute, a hard ceiling on the selected track attribute’s value can be provided. See tunable track attributes below for the list of available options. For example, max_instrumentalness=0.35 would filter out most tracks that are likely to be instrumental.

        Range: 0 - 1
        target_speechiness
        number
        For each of the tunable track attributes (below) a target value may be provided. Tracks with the attribute values nearest to the target values will be preferred. For example, you might request target_energy=0.6 and target_danceability=0.8. All target values will be weighed equally in ranking results.

        Range: 0 - 1
        min_tempo
        number
        For each tunable track attribute, a hard floor on the selected track attribute’s value can be provided. See tunable track attributes below for the list of available options. For example, min_tempo=140 would restrict results to only those tracks with a tempo of greater than 140 beats per minute.

        max_tempo
        number
        For each tunable track attribute, a hard ceiling on the selected track attribute’s value can be provided. See tunable track attributes below for the list of available options. For example, max_instrumentalness=0.35 would filter out most tracks that are likely to be instrumental.

        target_tempo
        number
        Target tempo (BPM)

        min_time_signature
        integer
        For each tunable track attribute, a hard floor on the selected track attribute’s value can be provided. See tunable track attributes below for the list of available options. For example, min_tempo=140 would restrict results to only those tracks with a tempo of greater than 140 beats per minute.

        Maximum value: 11
        max_time_signature
        integer
        For each tunable track attribute, a hard ceiling on the selected track attribute’s value can be provided. See tunable track attributes below for the list of available options. For example, max_instrumentalness=0.35 would filter out most tracks that are likely to be instrumental.

        target_time_signature
        integer
        For each of the tunable track attributes (below) a target value may be provided. Tracks with the attribute values nearest to the target values will be preferred. For example, you might request target_energy=0.6 and target_danceability=0.8. All target values will be weighed equally in ranking results.

        min_valence
        number
        For each tunable track attribute, a hard floor on the selected track attribute’s value can be provided. See tunable track attributes below for the list of available options. For example, min_tempo=140 would restrict results to only those tracks with a tempo of greater than 140 beats per minute.

        Range: 0 - 1
        max_valence
        number
        For each tunable track attribute, a hard ceiling on the selected track attribute’s value can be provided. See tunable track attributes below for the list of available options. For example, max_instrumentalness=0.35 would filter out most tracks that are likely to be instrumental.

        Range: 0 - 1
        target_valence
        number
        For each of the tunable track attributes (below) a target value may be provided. Tracks with the attribute values nearest to the target values will be preferred. For example, you might request target_energy=0.6 and target_danceability=0.8. All target values will be weighed equally in ranking results.

        Range: 0 - 1
'''
def create_API_Spotify(user_preferences):
    Spotify_API_prompt = f'''
            You need to use {user_preferences} to return a JSON-format object that is suitable for using with Spotify Music API to get recommendations.
            Extract the user's preferences from the {user_preferences} text. Analyze:
            
            1. Seed tracks: Exact names or IDs of songs. If not provided, use the text in the user_prompt to find recommendations. Limit to a max of 5.
            2. Seed artists: Names or IDs of artists. If not provided, use the text in the user_prompt to find recommendations. Limit to a max of 5.
            3. Seed genres: Relevant music genres. If not provided, use the text in the user_prompt to find recommendations. Limit to a max of 5.
            4. Optional features (if mentioned): The options are danceability, energy, tempo, and mood. Try to use as many of these as possible. Range is between 0 to 1. 

            Here's the format of the Spotify music API to get recommendations that you must strictly follow {SPOTIFY_API_FORMAT}. Pay close attention to the required parts of the JSON request, and conditional requirements based on presence or absence of other fields. 
            The response can be longer than this to ensure all the main preferences and sentiments are expressed, and the length can be any random value between 1 minute to 5 minutes. 
            The length can be adjusted based on {user_preferences} to gauge the average length of songs of such genre/type, and how long the music should be based on any other details you deem useful. 
    '''
    try:
        completion = client.chat.completions.create(
        model="meta-llama/Meta-Llama-3.1-405B-Instruct",
        messages=[{"role": "user", "content": Spotify_API_prompt}],
        temperature=0.8
        )
        return completion.choices[0].message.content
    except Exception as e:
        raise str(e)

def create_API_beetoven(user_preferences):
    beatoven_API_prompt = f'''
            You need to use {user_preferences} to create a short prompt for an AI tool that will generate a track for user. 
            It has to summarize the main ideas like genre, tone/mode, etc. of the {user_preferences}. Here is an example delimited by angle braces for the type of output you will be providing, you need to follow it strictly. 
            < 30 seconds peaceful lo-fi chill hop track >
            The response can be longer than this to ensure all the main preferences and sentiments are expressed, and the length can be any random value between 1 minute to 5 minutes. 
            The length can be adjusted based on {user_preferences} to gauge the average length of songs of such genre/type, and how long the music should be based on any other details you deem useful. 
    '''
    try:
        completion = client.chat.completions.create(
        model="meta-llama/Meta-Llama-3.1-405B-Instruct",
        messages=[{"role": "user", "content": beatoven_API_prompt}],
        temperature=0.8
        )
        return completion.choices[0].message.content
    except Exception as e:
        raise str(e)



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
