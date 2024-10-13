from openai import OpenAI

client = OpenAI(api_key=api_key)
import os
import json
import tiktoken as tk
import threading
import queue
import time
import logging

import executor
import worker

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise EnvironmentError("OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")

class Manager:
    def __init__(self, api_key: str, workers: int):
        self.task_queue = queue.Queue()  # Queue for tasks
        self.worker_queue = queue.Queue()  # Queue for available workers

        # Initialize worker threads
        self.workers = []
        for _ in range(workers):
            work = worker.Worker(api_key, self.task_queue, self.worker_queue)
            work.start()  # Start each worker thread
            self.workers.append(work)
            self.worker_queue.put(work)  # Initially all workers are available

        self.executor = executor.Executor(api_key)
        logging.info(f"Manager initialized with {workers} workers.")
        self.start()

    def originate_task(self) -> list:
        """ Reads content of README.md and creates a series of tasks for the workers """
        # check if README.md exists
        if not os.path.exists("README.md"):
            raise FileNotFoundError("README.md not found in the current directory.")
        with open("README.md", "r") as f:
            readme = f.read()
        encoding = tk.get_encoding("cl100k_base")
        readme_encoded = encoding.encode(readme)

        response = client.completions.create(engine="gpt-4",
        prompt=f"Given the following project:\n\n{readme}\n\nGenerate a series of tasks for the workers to complete.",
        temperature=0.5,
        max_tokens=1500,
        stop=["\n"])
        tasks = response.choices[0].text.strip()
        return tasks.split("\n")

    def start(self):
        """ Begin task generation and assignment process """
        orig_tasks = self.originate_task()
        for task in orig_tasks:
            self.add_task(task)

        # Main loop to monitor task completion and worker availability
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
