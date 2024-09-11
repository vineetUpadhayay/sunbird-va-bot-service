import json
from typing import (
    Dict,
    List
)
from env_manager import vectorstore_class
from utils.env import get_from_env_or_config
from redis_util import get_cache_data_from_redis
from logger import logger
from apscheduler.schedulers.background import BackgroundScheduler
import pytz

def move_to_ltm():
    """Index frequently asked query and response pairs in Long Term Memory"""
    indices_cached: dict = json.loads(get_from_env_or_config('database', 'indices_cached', None))
    indices_cached_ltm: dict = json.loads(get_from_env_or_config('database', 'indices_cached_ltm', None))
    
    for context in indices_cached.keys():
        cached_data = get_cache_data_from_redis(context)
        documents: List[Dict[str, str]] = []
        
        for query, response in cached_data:
            documents.append({
                "text": query,
                "metadata": json.dumps({
                            "response": response
                            })
            })

        index_id = indices_cached_ltm.get(context)
        if documents:
            ids = vectorstore_class.cache_documents(documents, index_id)
        logger.info({"Context ": context, "Indexing in LTM": "Successful"})

scheduler = BackgroundScheduler()
IST = pytz.timezone('Asia/Kolkata')
scheduler.add_job(move_to_ltm, 'cron', day_of_week='sun', hour=0, minute=0, timezone=IST)

def start_scheduler():
    scheduler.start()

def shutdown_scheduler():
    scheduler.shutdown()