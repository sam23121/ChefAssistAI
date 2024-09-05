# ChefAssistAI

![ChefAssistAI](assets/images/chefassistanai.webp)

A cooking assistant that leverages Retrieval-Augmented Generation (RAG) to provide comprehensive cooking guidance. This project doesn't need any credits and all llm providers are free.

## Overview

Navigating the culinary world can be daunting, especially for those new to cooking. Recipes often use unfamiliar terms, and finding trustworthy answers to specific food questions can be time-consuming.

ChefAssistAI serves as a virtual kitchen companion, utilizing cutting-edge AI to offer instant, reliable guidance on all things food-related. From ingredient substitutions to cooking techniques, this tool empowers both novices and seasoned chefs to explore the culinary arts with confidence.

### What ChefAssistAI Can Help With

ChefAssistAI is designed to assist with a wide range of culinary queries and tasks, including:

- Recipe information and cooking instructions
- Cuisine knowledge from various cultures
- Dietary information and meal planning
- Cooking techniques and equipment usage
- Ingredient substitutions and food pairings
- Spice levels and flavor profiles
- Serving suggestions and cultural context
- General cooking tips and tricks

Whether you're looking to try a new recipe, understand a cooking technique, or explore different cuisines, ChefAssistAI is your go-to culinary companion.

## Dataset

ChefAssistAI is powered by a comprehensive culinary dataset that includes:

- Detailed ingredient lists and cooking instructions
- Information on cooking techniques, equipment, and serving suggestions
- Cuisine classifications and cultural context for dishes
- Dietary information (e.g., vegetarian options, meal types)
- Spice level indicators and flavor profiles

The Dataset was generated using GPT-4 and is a collection of recipes, cooking techniques, ingredient information, and other culinary knowledge.

the prompt used to generate the dataset is:
```text
Give me a dataset with columns of the name of a food, country where it is prepared, ingredient, instructions, Meal Type,Spice Level,Cooking Time (minutes),Vegetarian,Main Cooking Method,Serving Temperature and how to make it of 10 rows. Make sure it is in a csv format and the delimiter is ;

```
if you like want you see add 100 rows more and more.

## Features

- Natural Language Query Handling: Users can ask questions about food, recipes, ingredients, and more
- Streamlit UI: A user-friendly web interface for interacting with the AI
- RAG (Retrieval-Augmented Generation): Combines retrieval of relevant information from a dataset That was generated using GPT-4 
- Real-time Monitoring: Uses Grafana to monitor response times, user queries, and system performance. postgres database to store the conversations and feedback
- Efficient Data Storage and Retrieval: Pinecone vector database stores and retrieves data efficiently using vector embeddings

## Technology Stack

- Language Models: Grok, OpenRouter (Free versions)
- Frontend: Streamlit
- Vector Database: Pinecone
- Monitoring Tool: Grafana and Postgres
- Programming Language: Python
- Containerization: Docker and Docker Compose


## Getting Started

### General Structure

The project is organized into the following directories:

- `app`: The source code for the project along with the docker file and docker compose file
- `data`: The food dataset
- `notebooks`: The notebooks used for data processing and created pinecone index as well as testing llm providers
- `assets`: The assets used in the project




### Prerequisites

Ensure you have the following installed:

- Python 3.8 or higher
- Streamlit
- Docker
- Docker Compose
- Pinecone Client Library
- Grafana
- API keys for Pinecone, Grok and OpenRouter



### Installation

### clone the repo

```bash
git clone https://github.com/sam23121/ChefAssistAI.git
cd ChefAssistAI/app
```

### Set Up Pinecone, Grok, and OpenRouter

Create a [Pinecone](https://docs.pinecone.io/guides/get-started/quickstart), [Groq](https://console.groq.com/keys) and [OpenRouter](https://openrouter.ai/models/meta-llama/llama-3.1-8b-instruct:free/api) account and obtain your API keys.

#### Set Up Environment Variables

Create a `.env` file in the root directory and add your API keys:

```bash
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_ENVIRONMENT=your-pinecone-environment
GROK_API_KEY=your-grok-api-key
OPENROUTER_API_KEY=your-openrouter-api-key
```


### Setup your vector database

Go to the notebooks folder and run the generate_embeds_and_test.ipynb notebook to create the pinecone index. or run the following code:
```python
import pinecone
import time
from tqdm.auto import tqdm
import pandas as pd
from sentence_transformers import SentenceTransformer

# Initialize Pinecone
pc = pinecone.Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
index_name = 'name that you want for your index' # you can also view it in pinecone console

existing_indexes = [
    index_info["name"] for index_info in pc.list_indexes()
]

# check if index already exists (it shouldn't if this is first time)
if index_name not in existing_indexes:
    # if does not exist, create index
    pc.create_index(
        index_name,
        dimension=384, 
        metric='dotproduct',
        spec=spec
    )
    # wait for index to be initialized
    while not pc.describe_index(index_name).status['ready']:
        time.sleep(1)

# connect to index
index = pc.Index(index_name)
time.sleep(1)
# view index stats
index.describe_index_stats()

for i in tqdm(range(0, len(df), batch_size)):
    # get end of batch
    i_end = min(len(df), i+batch_size)
    batch = df.iloc[i:i_end]
    
    # Combine all columns into a single text for each row
    documents = batch.apply(lambda row: ' '.join(row.astype(str).replace('nan', '')), axis=1).tolist()
    
    # Create document embeddings
    embeds = model.encode(documents)
    
    # Get IDs
    ids = batch['id'].tolist()
    # batch = batch.drop('id', axis=1)

    metadatas = batch.where(batch.notnull(), None).to_dict('records')


    for i, doc in enumerate(documents):
        metadatas[i]['text'] = doc
    
    # Create metadata, replacing NaN with None
    
    # Ensure all values are JSON serializable
    metadatas = [{k: (v if v is not None else "") for k, v in m.items()} for m in metadatas]

    vectors = [
        {
            'id': id,
            'values': embed.tolist(),
            'metadata': metadata
        }
        for id, embed, metadata in zip(ids, embeds, metadatas)
    ]
    
    # Add everything to pinecone
    # index.upsert(vectors=zip(ids, embeds, metadatas))
    index.upsert(vectors=vectors)
```

#### Replace all the env variables in the docker-compose.yml file with your own values
After you have setup your vector database, change the index name, api-key values in env, credintials in the docker-compose.yml file with your own values

#### Build and Run with Docker Compose

Now you can run the following command to start the application:

```bash
docker-compose up --build
```


This command will build the Docker images and start the containers for the Streamlit app, Grafana, and Postgres.

### Accessing the Application

- Streamlit App: Visit http://localhost:8501 in your browser. ![Streamlit](assets/images/streamlit.png)

- Grafana Dashboard: Visit http://localhost:3000 in your browser. ![Grafana](assets/images/grafana.png)

#### Meterics of Dashboard:


Here’s the description for each of the requested panels:

1. Average Feedback Score (Single Stat): Displays the average feedback score across all conversations. This panel provides an indication of overall user satisfaction with responses, with a higher score reflecting better feedback.

2. Feedback Rate (Percentage of Conversations with Feedback) (Single Stat): Shows the percentage of conversations where users provided feedback. This panel helps track user engagement in providing feedback, with higher percentages indicating more frequent user participation.

3. Average Total Tokens per Prompt (Single Stat): Displays the average number of tokens used per conversation, combining prompt and completion tokens. This metric helps monitor the efficiency of responses, indicating how many tokens are typically consumed for each user interaction.      

4. Percentage of High Relevance Responses (Donut Chart): A donut chart that visualizes the percentage of conversations deemed highly relevant. This panel helps assess the quality of responses, with higher percentages indicating more relevant answers provided to users.        

5. Average Prompt Tokens vs Completion Tokens (Donut Chart): This donut chart displays the distribution between prompt tokens and completion tokens used in conversations. In this visualization, 90% of the total tokens are used for prompts, while 10% are used for completions. This panel helps monitor the balance between user input and the model's response output, which can be useful for understanding token usage efficiency.

6. Average Response Time (Single Stat): Displays the average time (in seconds) it takes for the system to generate a response to a user query. In this case, the average response time is 1.87 seconds. This metric helps track the system's speed, allowing you to identify if there are any performance slowdowns.

7. Last 5 Conversations (Table): Displays a table showing the five most recent conversations, including details such as the question, answer, relevance, and timestamp. This panel helps monitor recent interactions with users.

8. +1/-1 (Pie Chart): A pie chart that visualizes the feedback from users, showing the count of positive (thumbs up) and negative (thumbs down) feedback received. This panel helps track user satisfaction.    

9. Relevancy (Gauge): A gauge chart representing the relevance of the responses provided during conversations. The chart categorizes relevance and indicates thresholds using different colors to highlight varying levels of response quality.

10. Tokens (Time Series): Another time series chart that tracks the number of tokens used in conversations over time. This helps to understand the usage patterns and the volume of data processed.

11. Model Used (Bar Chart): A bar chart displaying the count of conversations based on the different models used. This panel provides insights into which AI models are most frequently used.

12. Response Time (Time Series): A time series chart showing the response time of conversations over time. This panel is useful for identifying performance issues and ensuring the system's responsiveness.

if you want to have a dashboard like the one in the screenshot, you need to import the dashboard from the json file in the assets/dashboard folder.

## Evaluations

### Retrieval evaluation

Using Only vector search gave the following metrics:

- Hit rate: 88.8%
- MRR: 11.2%

Using Hybrid search gave the following metrics:

- Hit rate: 37%
- MRR: 6.2%

Which shows that vector search is better for this use case. (Maybe it was poor because of my implementation)



### RAG flow evaluation

I used the LLM-as-a-Judge metric to evaluate the quality of our RAG flow. The llm used was from groq using llama3.1-70b-versatile

in a sample with 200 records, I had:

- (81%) RELEVANT
- (14.6%) PARTLY_RELEVANT
- (0.4%) NON_RELEVANT


## Background

Below are the explanations for the key components in the project. This projects can be built with no credits and all llm providers are free.

### Docker and Docker Compose: A Detailed Explanation

Docker and Docker Compose are used in this project to containerize the application, making it easy to deploy and run consistently across different environments.


#### Key Components in Docker Compose

The `docker-compose.yml` file defines the following services:

1. `app`: The Streamlit application
2. `grafana`: The Grafana monitoring dashboard
3. `postgres`: The PostgreSQL database for storing conversation logs and metrics

#### How Docker Works in This Project

1. The Streamlit app, Grafana, and Postgres are each defined as separate services in the Docker Compose file.
2. When you run `docker-compose up`, it builds and starts all the containers.
3. The containers are networked together, allowing them to communicate with each other.
4. Volumes are used to persist data for Grafana and Postgres.
5. Environment variables are passed to the containers for configuration.

Using Docker and Docker Compose simplifies the deployment process and ensures that all components of the ChefAssistAI project work together seamlessly.


### 3 Pinecone: A Detailed Explanation

Pinecone is a fully managed vector database that makes it easy to work with vector embeddings. It's optimized for storing and querying large amounts of vector data, which is essential for applications like Chef Assistant AI that rely on retrieval-augmented generation.


#### How Pinecone Works in This Project

In the Chef Assistant AI project:

1. Pinecone stores vector embeddings of the food dataset.
2. When a user query is received, the query is converted into a vector embedding.
3. Pinecone retrieves the most relevant embeddings from the dataset based on the query vector.
4. The retrieved data is then passed to GPT-4 to generate a context-aware response.

## Contributing

We welcome contributions! Please read our Contributing Guide for details on how to contribute to the project.

## License

This project is licensed under the MIT License - see the LICENSE file for details.


