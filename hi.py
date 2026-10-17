from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser


llm = ChatOllama(
    model="gemma3:1b",
    temperature=0.7,
)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a helpful assistant."),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{question}"),
    ]
)

chat_history = []

chain = prompt | llm | StrOutputParser()

def chat(question: str) -> str:
    try:
        result = chain.invoke(
            {
                "question": question, 
                "chat_history": chat_history
            })
    except Exception as e:
        result = f"Error: {str(e)}"

    chat_history.append(HumanMessage(content=question))
    chat_history.append(AIMessage(content=result))
    
    return result

# Intractive chat loop
if __name__ == "__main__":
    print("Welcome to the open chat! Type 'exit' to quit.")
    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            print("Exiting the chat. Goodbye!")
            break
        response = chat(user_input)
        print(f"Bot: {response}")