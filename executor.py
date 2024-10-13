import openai
import json
import tiktoken as tk
import os

# Fetch API key from environment
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise EnvironmentError("OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")
openai.api_key = api_key

# Object that executes a series of commands on the host machine
commands_desc = {
    "/newfile <filename>": "Create a new file",
    "/edit <filename> <task>": "Write code to a file",
    "/terminate": "Task is completed"
}
command_list = list(commands_desc.keys())

class Executor:
    def __init__(self, api_key: str):
        self.encoding = tk.get_encoding("cl100k_base")

    def decide(self, ctx, task) -> int:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an assistant deciding the appropriate action based on the task."},
                {"role": "user", "content": f"Given the following project:\n\n{ctx}\n\nAnd given the task by your manager: {task}\n\nPlease choose the appropriate action: {commands_desc}"}
            ],
            temperature=0.5,
            max_tokens=1500,
            stop=["\n"]
        )
        choice = response.choices[0].message["content"].strip()
        return int(choice)

    def parse(self, choice) -> list:
        tokens = choice.split(" ")
        if tokens[0] not in command_list:
            print("Invalid command, level 1")
            return None
        if "/newfile" in tokens:
            if len(tokens) != 2:
                print("Invalid syntax, newfile")
                return None
            return ["/newfile", tokens[1]]

        elif "/edit" in tokens[0]:
            if len(tokens) < 3:
                print("Invalid syntax, edit")
                return -1
            filename = tokens[1]
            task = tokens[2:]
            return ["/edit", filename, task]

        elif "/terminate" in tokens[0]:
            return ["/terminate"]

    def extract_ctx(self) -> dict:
        root = os.getcwd()
        ctx = {}
        exclude_dirs = {".venv", "venv", "__pycache__", "node_modules", ".git", ".hg", ".svn", ".idea", ".vscode", "build", "dist", "target"}
        
        for current_root, dirs, files in os.walk(root):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            for file in files:
                file_path = os.path.join(current_root, file)
                with open(file_path, "r") as f:
                    ctx[file] = self.encoding.encode(f.read())
        return ctx
