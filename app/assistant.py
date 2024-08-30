import json
from openai import OpenAI
import os
import torch
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
import time
import requests
from groq import Groq

from dotenv import load_dotenv

# Load the environment variables from the .env file
load_dotenv(dotenv_path="../.env")
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY") 
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')



device = 'cuda' if torch.cuda.is_available() else 'cpu'
model = SentenceTransformer('all-MiniLM-L6-v2', device=device)
# model = SentenceTransformer('all-MiniLM-L6-v2')



openrouter_client = OpenAI(
  api_key = OPENROUTER_API_KEY,
  base_url = "https://openrouter.ai/api/v1",
)

groq_client = Groq(
  api_key=GROQ_API_KEY
)



pc = Pinecone(api_key=PINECONE_API_KEY)

index_name = 'semantic-search'
# connect to index
index = pc.Index(index_name)




def query_pinecone(query, top_k=5):
    xq = model.encode(query).tolist()
    xc = index.query(vector=xq, top_k=top_k, include_metadata=True)
    results = []
    for match in xc.matches:
        result = {
            "id": match.id,
            "score": match.score,
            "metadata": match.metadata
        }
        if result["score"] > 0.2:
            results.append(result)
            # print(results)
    
    return results

def format_dish_info(dish):
    return "\n".join([f"{key}: {value}" for key, value in dish['metadata'].items() if value])

def query_openrouter(prompt):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENROUTER_API_KEY}"
    }
    
    data = {
        "model": "meta-llama/llama-3.1-8b-instruct:free",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 150,
        "temperature": 0.0
    }
    
    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
    # print(response.json())
    return response.json()['choices'][0]['message']['content']

def qa_function(question, model_choice):
    # Query Pinecone
    results = query_pinecone(question)
    # print(results)
    if not results:
        return "I'm sorry, I couldn't find any relevant information to answer your question."
    
    # Format the dish information
    all_dish_info = "\n\n".join([format_dish_info(dish) for dish in results])

    # print(all_dish_info)
    
    # Create the prompt
    prompt = f"""
    Based on the following information about a dish, please answer the question: {question}

    Dish information:
    {all_dish_info}

    Answer:
    """
    
    # Use OpenRouter to generate an answer
    answer, tokens, response_time = llm(prompt, model_choice)
    
    relevance, explanation, eval_tokens = evaluate_relevance(prompt, answer)

    
    return {
        'answer': answer,
        'response_time': response_time,
        'relevance': relevance,
        'relevance_explanation': explanation,
        'model_used': model_choice,
        'prompt_tokens': tokens['prompt_tokens'],
        'completion_tokens': tokens['completion_tokens'],
        'total_tokens': tokens['total_tokens'],
        'eval_prompt_tokens': eval_tokens['prompt_tokens'],
        'eval_completion_tokens': eval_tokens['completion_tokens'],
        'eval_total_tokens': eval_tokens['total_tokens'],
    }




def llm(prompt, model_choice):
    start_time = time.time()
    if model_choice.startswith('openrouter'):  
        response = openrouter_client.chat.completions.create(
            messages=[{"role": "user","content": prompt}],
            model="meta-llama/llama-3.1-8b-instruct:free",
            )
        answer = response.choices[0].message.content
        tokens = {
            'prompt_tokens': response.usage.prompt_tokens,
            'completion_tokens': response.usage.completion_tokens,
            'total_tokens': response.usage.total_tokens
        }
    elif model_choice.startswith('groq'):
        response = groq_client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )
        answer = response.choices[0].message.content
        tokens = {
            'prompt_tokens': response.usage.prompt_tokens,
            'completion_tokens': response.usage.completion_tokens,
            'total_tokens': response.usage.total_tokens
        }
    else:
        raise ValueError(f"Unknown model choice: {model_choice}")
    
    end_time = time.time()
    response_time = end_time - start_time
    
    return answer, tokens, response_time


def evaluate_relevance(question, answer):
    prompt_template = """
    You are an expert evaluator for a Retrieval-Augmented Generation (RAG) system.
    Your task is to analyze the relevance of the generated answer to the given question.
    Based on the relevance of the generated answer, you will classify it
    as "NON_RELEVANT", "PARTLY_RELEVANT", or "RELEVANT".

    Here is the data for evaluation:

    Question: {question}
    Generated Answer: {answer}

    Please analyze the content and context of the generated answer in relation to the question
    and provide your evaluation in parsable JSON without using code blocks and make sure it is json parsable and nothing else is added
    to the below structure:

    {{
      "Relevance": "NON_RELEVANT" | "PARTLY_RELEVANT" | "RELEVANT",
      "Explanation": "[Provide a brief explanation for your evaluation]"
    }}
    """.strip()

    prompt = prompt_template.format(question=question, answer=answer)
    evaluation, tokens, _ = llm(prompt, 'groq')
    
    try:
        json_eval = json.loads(evaluation)
        return json_eval['Relevance'], json_eval['Explanation'], tokens
    except json.JSONDecodeError:
        return "UNKNOWN", "Failed to parse evaluation", tokens



