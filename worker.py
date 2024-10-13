import openai as OpenAI
import os
import tiktoken as tk
import threading
import logging
import executor

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# Fetch API key from environment
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise EnvironmentError("OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")

# Set API key for OpenAI client
client = OpenAI.Client(api_key=api_key)

class Worker(threading.Thread):  # Inherit from threading.Thread for concurrent execution
    def __init__(self, api_key: str, task_queue, worker_queue):
        super().__init__()
        self.encoding = tk.get_encoding("cl100k_base")
        self.executor = executor.Executor(api_key)
        self.task_queue = task_queue
        self.worker_queue = worker_queue
        self.daemon = True
    
    def run(self):
        """ Continuously fetch tasks and process them in a loop """
        logging.info(f"Worker {self.name} started and waiting for tasks.")
        while True:
            task = self.task_queue.get()
            if task is None:
                logging.info(f"Worker {self.name} received shutdown signal.")
                break
            try:
                logging.info(f"Worker {self.name} is processing task: {task}")
                self.accept_task(task)
                logging.info(f"Worker {self.name} completed task: {task}")
            except Exception as e:
                logging.error(f"Error processing task {task} by Worker {self.name}: {e}")
            finally:
                # Add the worker back to the worker queue once the task is done
                self.worker_queue.put(self)
                self.task_queue.task_done()

    def accept_task(self, task: str):
        command_list = self.executor.parse(self.executor.decide(task))
        if command_list is None:
            logging.info(f"Worker {self.name} found nothing to be done for task: {task}")
            return
        if command_list[0] == "/newfile":
            with open(command_list[1], "w") as f:
                f.write("")
        elif command_list[0] == "/edit":
            self.write_code(command_list[1], command_list[2])
        elif command_list[0] == "/terminate":
            logging.info(f"Worker {self.name} received terminate command.")
            return

    def write_code(self, file: str, task: str):
        try:
            with open(file, "r") as f:
                code = f.read()
            with open(f"{file}.bak", "w") as backup:
                backup.write(code)

            logging.info(f"Worker {self.name} is editing file {file} for task: {task}")
            token_count = self.count_tokens(code)
            user_input = f"Here is the current code:\n{code}\n\nYour task: {task}"

            response = client.ChatCompletion.create(
                model="gpt-4",  
                messages=[
                    {"role": "system", "content": "You are a code generator. Write code to solve the given task."},
                    {"role": "user", "content": user_input}
                ],
                max_tokens=1500,
                temperature=0.5
            )

            generated_code = response.choices[0].message["content"]
            with open(file, "w") as f:
                f.write(generated_code)
            logging.info(f"Worker {self.name} successfully edited {file} for task: {task}")
        except Exception as e:
            logging.error(f"Error editing file {file} by Worker {self.name}: {e}")

    def count_tokens(self, text: str) -> int:
        return len(self.encoding.encode(text))
