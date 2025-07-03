import psycopg2
from psycopg2.extras import RealDictCursor
from bot_config import DB_CONFIG

def get_conn():
    return psycopg2.connect(**DB_CONFIG)

def create_table():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute('''
                CREATE TABLE IF NOT EXISTS subscribers (
                    id BIGINT PRIMARY KEY,
                    name TEXT,
                    subscription BOOLEAN
                )
            ''')
            conn.commit()

def add_or_update_subscriber(user_id, name, subscription):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute('''
                INSERT INTO subscribers (id, name, subscription)
                VALUES (%s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET name=EXCLUDED.name, subscription=EXCLUDED.subscription
            ''', (user_id, name, subscription))
            conn.commit()

def get_subscription_status(user_id):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('SELECT subscription FROM subscribers WHERE id=%s', (user_id,))
            row = cur.fetchone()
            return row['subscription'] if row else None 