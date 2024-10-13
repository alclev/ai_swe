from openai import OpenAI

client = OpenAI(api_key=api_key)
import os
import json
import tiktoken as tk

# Object that executs a series of commands on the host machine

# 1. Write code to a file
# 2. Read code from a file
# 3. Version control
# 6. Debug code
# 7. Test code
# 8. Refactor code
# 9. Optimize code
# 10. Document code

commands_desc = {"/newfile <filename>": "Create a new file",
           "/edit <filename> <task>": "Write code to a file",
        #    "/git <commands>": "Version control",
           "/terminate" : "Task is completed"} 
command_list = list(commands_desc.keys())           

class Executor:
    def __init__(self, api_key: str):
        self.encoding = tk.get_encoding("cl100k_base")


    def decide(self, ctx, task) -> int:
        response = client.completions.create(engine="gpt-4",
        prompt=f""" Given the following project:\n\n{ctx}\n\nAnd given the following task by your 
            manager: {task} \n\n Please choose the appropriate action to take: \n\n {commands_desc}""",
        temperature=0.5,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0,
        stop=["\n"])
        choice = response.choices[0].text.strip()
        return int(choice)

    def parse(self, choice) -> list:
        tokens = choice.split(" ")
        if tokens[0] not in command_list:
            print("Invalid command, level 1")
            return None
        if "/newfile" in tokens:
            if(len(tokens) != 2):
                print("Invalid syntax, newfile")
                return None
            return ["/newfile", tokens[1]]

        elif "/edit" in tokens[0]:
            if(len(tokens) < 3):
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
        exclude_dirs = {".venv, venv, __pycache__, node_modules, .git, .hg, .svn, .idea, .vscode, build, dist, target"}
        for current_root, dirs, files in os.walk(root):
            # Exclude certain directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]

            for file in files:
                file_path = os.path.join(current_root, file)
                with open(file_path, "r") as f:
                    ctx[file] = self.encoding.encode(f.read()) #tk.get_encoding(f.read())
        return ctx