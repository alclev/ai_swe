import openai as OpenAI
import os
import tiktoken as tk
import executor

# Fetch API key from environment
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise EnvironmentError("OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")

# Set API key for OpenAI client
OpenAI.api_key = api_key

# Worker class definition
class Worker:
    def __init__(self, api_key: str):
        # Initialize the OpenAI client
        self.client = OpenAI(api_key=api_key)
        self.encoding = tk.get_encoding("cl100k_base")  
        self.executor = executor.Executor(api_key)
    
    def accept_task(self, task: str):
        command_list = executor.parse(executor.decide(task))
        if command_list is None:
            print("Nothing to be done.")
            return
        if command_list[0] == "/newfile":
            with open(command_list[1], "w") as f:
                f.write("")
        elif command_list[0] == "/edit":
            self.write_code(command_list[1], command_list[2])

        elif command_list[0] == "/terminate":
            print("Task terminated.")
            return

    def count_tokens(self, text: str) -> int:
        """
        Utility to count the number of tokens in the input text.
        """
        return len(self.encoding.encode(text))

    def write_code(self, file: str, task: str):
        """
        This function reads a code file, sends it to the OpenAI GPT-4 model for modifications, 
        and writes the modified code back to the file.
        :param file: Path to the code file.
        :param task: Task description for the model.
        """
        # Read the file content
        with open(file, "r") as f:
            code = f.read()

        # Check token usage
        token_count = self.count_tokens(code)
        print(f"Token count for file content: {token_count}")
        
        # Prepare prompt for GPT-4 model
        user_input = f"Here is the current code:\n{code}\n\nYour task: {task}"

        try:
            response = self.client.ChatCompletion.create(
                model="gpt-4",  # Use GPT-4 instead of gpt-4o for text completions
                messages=[
                    {"role": "system", "content": "You are a code generator. Write code to solve the given task."},
                    {"role": "user", "content": user_input}
                ],
                max_tokens=1500,  # Adjust max tokens based on expected output length
                temperature=0.5
            )

            # Extract the response
            generated_code = response.choices[0].message["content"]
            print("Generated code:", generated_code)

        except Exception as e:
            print(f"Error: {str(e)}")

        # Write the response back to the file
        with open(file, "w") as f:
            f.write(generated_code)

