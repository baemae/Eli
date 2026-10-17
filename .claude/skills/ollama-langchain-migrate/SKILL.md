# Migrate Ollama SDK to LangChain

This skill guides the migration of a chat implementation from the native Ollama Python SDK to LangChain.

## Overview

LangChain provides a unified interface for interacting with various LLMs, including Ollama. Migrating to LangChain allows for easier model swapping, better state management (memory), and seamless integration with tools and agents.

## Migration Steps

### 1. Install Dependencies
Ensure you have the necessary LangChain packages installed:
```bash
uv add langchain-ollama langchain
```

### 2. Replace Model Initialization
**From (Ollama SDK):**
```python
import ollama
client = ollama.Client()
# response = client.chat(model='gemma3:1b', messages=[...])
```

**To (LangChain):**
```python
from langchain_ollama import ChatOllama

llm = ChatOllama(
    model="gemma3:1b",
    temperature=0,
)
```

### 3. Update Message Formatting
LangChain uses specific message classes instead of raw dictionaries.

- `SystemMessage` for system prompts.
- `HumanMessage` for user input.
- `AIMessage` for model responses.

**Example:**
```python
from langchain_core.messages import HumanMessage, SystemMessage

messages = [
    SystemMessage(content="You are a helpful AI assistant"),
    HumanMessage(content="Hi!")
]
response = llm.invoke(messages)
print(response.content)
```

### 4. Implement Streaming
LangChain provides a `.stream()` method for real-time output.

```python
for chunk in llm.stream(messages):
    print(chunk.content, end="", flush=True)
```

### 5. Add Memory (Conversation History)
Instead of manually managing a list of dictionaries, use LangChain's memory utilities or simply maintain a list of message objects.

```python
history = [SystemMessage(content="You are a helpful AI assistant")]

while True:
    user_input = input("You: ")
    history.append(HumanMessage(content=user_input))
    
    response = llm.invoke(history)
    print(f"Bot: {response.content}")
    history.append(response)
```

## Verification Checklist
- [ ] Model initializes without errors.
- [ ] Chat history is preserved across turns.
- [ ] Streaming output is functional.
- [ ] Model response content is correctly extracted using `.content`.
