import psycopg2
import time
import os
from datetime import datetime
from zoneinfo import ZoneInfo

tz = ZoneInfo("Africa/Addis_Ababa")

def get_db_connection():
    """
    Establishes and returns a connection to the PostgreSQL database.
    """
    try:
        # Replace with your actual PostgreSQL database credentials
        return psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "db"),
            database=os.getenv("POSTGRES_DB", "food_assistant"),
            user=os.getenv("POSTGRES_USER", "sam"),
            password=os.getenv("POSTGRES_PASSWORD", "sam123"),
        )
    except psycopg2.Error as e:
        print(f"An error occurred while connecting to the database: {e}")
        return None

def init_db():
    """
    Initializes the database by creating required tables.
    """
    conn = get_db_connection()
    if conn is None:
        return
    try:
        cur = conn.cursor()
        cur.execute("DROP TABLE IF EXISTS feedback")
        cur.execute("DROP TABLE IF EXISTS conversations")

        cur.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                _id SERIAL PRIMARY KEY,
                id VARCHAR NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                model_used TEXT NOT NULL,
                response_time FLOAT NOT NULL,
                relevance TEXT NOT NULL,
                relevance_explanation TEXT NOT NULL,
                prompt_tokens INTEGER NOT NULL,
                completion_tokens INTEGER NOT NULL,
                total_tokens INTEGER NOT NULL,
                eval_prompt_tokens INTEGER NOT NULL,
                eval_completion_tokens INTEGER NOT NULL,
                eval_total_tokens INTEGER NOT NULL,
                timestamp TIMESTAMP NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id SERIAL PRIMARY KEY,
                conversation_id VARCHAR REFERENCES conversations(id),
                feedback INTEGER NOT NULL,
                timestamp TIMESTAMP NOT NULL
            )
        """)
        conn.commit()
    except psycopg2.Error as e:
        print(f"An error occurred during database initialization: {e}")
    finally:
        conn.close()

def save_conversation(conversation_id, question, answer_data, timestamp=None):
    """
    Saves a conversation record to the database.
    """
    if timestamp is None:
        timestamp = datetime.now(tz)

    conn = get_db_connection()
    if conn is None:
        return
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO conversations 
            (id, question, answer, model_used, response_time, relevance, 
            relevance_explanation, prompt_tokens, completion_tokens, total_tokens, 
            eval_prompt_tokens, eval_completion_tokens, eval_total_tokens, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                conversation_id,
                question,
                answer_data["answer"],
                answer_data["model_used"],
                answer_data["response_time"],
                answer_data["relevance"],
                answer_data["relevance_explanation"],
                answer_data["prompt_tokens"],
                answer_data["completion_tokens"],
                answer_data["total_tokens"],
                answer_data["eval_prompt_tokens"],
                answer_data["eval_completion_tokens"],
                answer_data["eval_total_tokens"],
                timestamp,
            )
        )
        conn.commit()
        print(f"Conversation {conversation_id} saved successfully")
    except psycopg2.Error as e:
        print(f"An error occurred while saving conversation: {e}")
        conn.rollback()
    finally:
        conn.close()

def save_feedback(conversation_id, feedback, timestamp=None, max_retries=3):
    """
    Saves a feedback record to the database.
    """
    if timestamp is None:
        timestamp = datetime.now(tz)

    for attempt in range(max_retries):
        conn = get_db_connection()
        if conn is None:
            return
        try:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO feedback (conversation_id, feedback, timestamp) VALUES (%s, %s, %s)",
                (conversation_id, feedback, timestamp),
            )
            conn.commit()
            print(f"Feedback saved successfully for conversation {conversation_id}")
            return True
        except psycopg2.Error as e:
            print(f"Attempt {attempt + 1}: An error occurred while saving feedback: {e}")
            conn.rollback()
            if attempt < max_retries - 1:
                time.sleep(0.5)  # Wait for 0.5 seconds before retrying
        finally:
            conn.close()
    
    print(f"Failed to save feedback after {max_retries} attempts")
    return False

def get_recent_conversations(limit=5, relevance=None):
    """
    Retrieves recent conversations with an optional relevance filter.
    """
    conn = get_db_connection()
    if conn is None:
        return []
    try:
        cur = conn.cursor()
        query = """
            SELECT 
                c.id, c.question, c.answer, c.model_used, c.response_time,
                c.relevance, c.relevance_explanation, c.prompt_tokens, c.completion_tokens,
                c.total_tokens, c.eval_prompt_tokens, c.eval_completion_tokens, c.eval_total_tokens,
                c.timestamp, f.feedback
            FROM conversations c
            LEFT JOIN feedback f ON c.id = f.conversation_id
        """
        params = []
        if relevance:
            query += " WHERE c.relevance = %s"
            params.append(relevance)
        query += " ORDER BY c.timestamp DESC LIMIT %s"
        params.append(limit)

        cur.execute(query, tuple(params))
        return cur.fetchall()
    except psycopg2.Error as e:
        print(f"An error occurred while fetching recent conversations: {e}")
        return []
    finally:
        conn.close()

def get_feedback_stats():
    """
    Retrieves statistics for feedback.
    """
    conn = get_db_connection()
    if conn is None:
        return None
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                SUM(CASE WHEN feedback > 0 THEN 1 ELSE 0 END) as thumbs_up,
                SUM(CASE WHEN feedback < 0 THEN 1 ELSE 0 END) as thumbs_down
            FROM feedback
        """)
        return cur.fetchone()
    except psycopg2.Error as e:
        print(f"An error occurred while fetching feedback stats: {e}")
        return None
    finally:
        conn.close()
