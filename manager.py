# Manager object that uses openai endpoint to manage the worker objects who serve as the 
# software engineers in the overall project.

import openai
import os
import json
import tiktoken as tk
import threading
import queue
import time

import executor

api_key = os
if not api_key:
    raise EnvironmentError("OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")

class Manager:
    def __init__(self, api_key: str, workers: list):
        openai.api_key = api_key
        # Create queue of available workers from list
        self.workers = queue.Queue()
        for worker in workers:
            self.workers.put(worker)

        # Create a queue of tasks
        self.tasks = queue.Queue()
        self.executor = executor.Executor(api_key)
        self.start()

    def originate_task(self) -> list:
        """ Reads content of readme file and creates a series of tasks for the workers"""
        
        # Read readme given that it exists
        with open("README.md", "r") as f:
            readme = f.read()
        readme = tk.get_encoding(readme)
        
        response = openai.Completion.create(
            engine="gpt-4",
            prompt=f""" Given the following project:\n\n{readme}\n\nPlease generate a series of tasks for the workers
            to complete. The tasks presented as a NEWLINE SEPARATED LIST.""",
            temperature=0.5,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0,
            stop=["\n"]
        )
        tasks = response.choices[0].text.strip()
        return tasks.split("\n")
    
    def breakdown_tasks(self, task: str) -> list: 
        response = openai.Completion.create(
            engine="gpt-4",
            prompt=f""" Given the following task: {task}\n\nPlease break down into a technically detailed
                 list of actionable subtasks. Present as a NEWLINE SEPARATED LIST.""",
            temperature=0.75,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0,
            stop=["\n"]
        )
        response.choices[0].text.strip()
        return response.split("\n")
    
    def tokenize(self, tasks: list) -> list:
        total = []
        for task in tasks: 
            sub_list = self.break_down_tasks(task)
            for subtask in sub_list:
                # Tokenize the subtask
                total.append(tk.get_encoding(subtask))
        return total
        
    
    def assess(self): 
        ctx = self.executor.extract_ctx()
        with open("README.md", "r") as f:
            readme = f.read()
        readme = tk.get_encoding(readme)

        response = self.client.ChatCompletion.create(
                model="gpt-4",  # Use GPT-4 instead of gpt-4o for text completions
                messages=[
                    {"role": "system", "content": f"You are a project manager. Here is the project context: {readme}"},
                    {"role": "user", "content": "Here is the current state of the project: \n\n" + json.dumps(ctx)
                    + """\n\nPlease return one of the following: 1. A newline separated list of tasks thats still need to be done
                    2. /terminate (to indicate the project is complete)"""}
                ],
                max_tokens=1500, 
                temperature=0.5
            )
        response = response.choices[0].message.content
        if(response == "/terminate"):
            return None
        else:
            tasks = response.split("\n")
            # Tokenize the tasks
            for task in tasks:
                self.tasks.put(tk.get_encoding(task))
            tasks.append("/review")
            return tasks
        
    def start(self):
        orig_tasks = self.originate_task()
        tasks = self.tokenize(orig_tasks)
        tasks.append("/review")
        # Start the main event loop
        while True:
            try:
                task = self.tasks.get_nowait()
                if(task == "/review"):
                    cond = self.assess()
                    if(cond is None):
                        print("Project complete.")
                        break
                    else:
                        continue
                    
                avail_worker = self.workers.get_nowait()
                avail_worker.accept_task(task)
            except Exception as e:
                print(f"Error: {str(e)}")
                time.sleep(5)
                break

    


    