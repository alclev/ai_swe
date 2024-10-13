import openai
import os
import tiktoken as tk
import threading
import queue
import time
import logging

import executor
import worker

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# Fetch API key from environment
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise EnvironmentError("OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")
openai.api_key = api_key

class Manager:
    def __init__(self, api_key: str, workers: int):
        self.task_queue = queue.Queue()
        self.worker_queue = queue.Queue()

        # Initialize worker threads
        self.workers = []
        for _ in range(workers):
            work = worker.Worker(api_key, self.task_queue, self.worker_queue)
            work.start()
            self.workers.append(work)
            self.worker_queue.put(work)

        self.executor = executor.Executor(api_key)
        logging.info(f"Manager initialized with {workers} workers.")
        self.start()

    def originate_task(self) -> list:
        """ Reads content of README.md and creates a series of tasks for the workers """
        if not os.path.exists("README.md"):
            raise FileNotFoundError("README.md not found in the current directory.")
        with open("README.md", "r") as f:
            readme = f.read()

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Generate a series of tasks based on the project."},
                {"role": "user", "content": f"Given the following project:\n\n{readme}\n\nGenerate tasks for the workers."}
            ],
            temperature=0.5,
            max_tokens=1500,
            stop=["\n"]
        )

        tasks = response.choices[0].message["content"].strip()
        return tasks.split("\n")

    def start(self):
        orig_tasks = self.originate_task()
        for task in orig_tasks:
            self.add_task(task)

        while True:
            try:
                if self.task_queue.empty():
                    logging.info("No tasks available.")
                    time.sleep(2)
                else:
                    avail_worker = self.worker_queue.get(timeout=10)
                    logging.info(f"Assigning task to worker: {avail_worker}")
            except queue.Empty:
                logging.info("No workers available, waiting...")
                time.sleep(5)

    def add_task(self, task: str):
        logging.info(f"Adding task: {task}")
        self.task_queue.put(task)
