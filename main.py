import openai as OpenAI
import os
import queue
import argparse
import manager
import executor
import worker

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise EnvironmentError("OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")

client = OpenAI(api_key=api_key)

# Function to parse CLI arguments, expecting ./main.py -g <git_repo_url> -w <worker_count>
def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dir", help="Root directory")
    parser.add_argument("-w", "--workers", help="Number of workers")
    args = parser.parse_args()
    return args.git, args.workers

# Manager should be in charge of assigning tasks to workers

if __name__ == '__main__':
    url, worker_count = parseArgs()
   
    # Creat a list of workers
    workers = []
    for i in range(worker_count):
        workers.append(worker.Worker(api_key))

    manager = manager.Manager(api_key, workers)

    # Main event loop
    while True:
        try:
            usr_input = input("Enter task: ")

        except KeyboardInterrupt:
            print("Exiting...")
            break
