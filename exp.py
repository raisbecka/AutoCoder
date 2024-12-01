from typing import List, Dict
import json
import ollama
import subprocess

# Tool definition for run_command
run_command_definition = {
    "type": "function",
    "function": {
        "name": "run_command",
        "description": "Runs a provided command on the system",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The command to be executed"
                }
            },
            "required": ["command"]
        }
    }
}

# List of tools to provide to Ollama
tools = [run_command_definition]

def run_command(command: str) -> Dict:
    """
    Runs a specified command as a subprocess and returns the result.
    
    Args:
        command: The command to execute
        
    Returns:
        Dict containing return code and combined stdout/stderr output
    """
    try:
        # Run command and capture output
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Get stdout and stderr
        stdout, stderr = process.communicate()
        
        # Combine output
        output = stdout + stderr
        
        return {
            "return_code": process.returncode,
            "output": output.strip()
        }
    except Exception as e:
        return {
            "return_code": 1,
            "output": f"Error executing command: {str(e)}"
        }

def test_ollama_tool_calling():
    try:
        # Initialize conversation history
        messages = [{
            "role": "user",
            "content": "What files are in the current directory? Use the run_command tool to find out."
        }]
        
        while True:
            # Make the request using ollama client
            response = ollama.chat(
                model='qwq',
                messages=messages,
                tools=tools,
                stream=False
            )
            
            # Check if tool call is requested
            if "tool_calls" in response:
                for tool_call in response["tool_calls"]:
                    if tool_call["function"]["name"] == "run_command":
                        # Parse tool call parameters
                        params = json.loads(tool_call["function"]["arguments"])
                        
                        # Execute the command
                        result = run_command(params["command"])
                        
                        # Add tool call and result to conversation
                        messages.append({
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [tool_call]
                        })
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "name": "run_command",
                            "content": json.dumps(result)
                        })
                        
                        # Continue conversation with tool results
                        continue
            
            # Add model's response to conversation history
            messages.append({
                "role": "assistant",
                "content": response["content"]
            })
            
            # Print final response
            print("Final Response:", json.dumps(response, indent=2))
            break
            
    except Exception as e:
        print(f"Error during Ollama chat: {e}")

if __name__ == "__main__":
    test_ollama_tool_calling()
