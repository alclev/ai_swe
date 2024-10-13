#!/usr/bin/env python3

import openai as OpenAI
import os
import argparse
import manager
import logging

import worker
import manager

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise EnvironmentError("OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")
client = OpenAI.Client(api_key=api_key)

# Function to parse CLI arguments, expecting ./main.py -d <directory> -w <worker_count>
def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dir", help="Root directory", required=True)
    parser.add_argument("-w", "--workers", help="Number of workers", type=int, required=True)
    args = parser.parse_args()
    if(int(args.workers) < 1 or int(args.workers) > 10):
        raise ValueError("Worker count must be between 1 and 10.")
    # Check if the directory exists, if not, create it
    if not os.path.exists(args.dir):
        os.makedirs(args.dir)
    # Change the current working directory to the specified directory
    os.chdir(args.dir)
    return args.dir, args.workers

# Entry point for the application
if __name__ == '__main__':
    root_dir, worker_count = parseArgs()

    # Initialize the manager with the number of workers
    logging.info(f"Starting Manager with {worker_count} workers.")
    manager_instance = manager.Manager(api_key, worker_count)

    # Main loop could also accept dynamic tasks
    while True:
        try:
            usr_input = input("Enter a new task (or type 'exit' to quit)> ")
            if usr_input.lower() == "exit":
                logging.info("Shutting down the manager.")
                break
            else:
                logging.info(f"Adding new task from user input: {usr_input}")
                manager_instance.add_task(usr_input)  # Dynamically adding tasks
            
        except KeyboardInterrupt:
            logging.info("KeyboardInterrupt received, shutting down.")
            break
