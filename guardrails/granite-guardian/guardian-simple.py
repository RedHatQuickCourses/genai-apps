import requests
import json

OLLAMA_URL = "http://localhost:11434/api/chat"
GUARDRAIL_MODEL = "granite3-guardian:2b"

def ollama_gen(messages):
    r = requests.post(
        OLLAMA_URL,
        json={
            "model": GUARDRAIL_MODEL, 
            "messages": messages, 
            "stream": True, 
            "options" : {
                "num_ctx" : 1024*8,
                "temperature" : 0,
                "seed": 42}
            },
            stream=False)
    r.raise_for_status()
    output = ""

    #print(f"Raw response =  {r.text}")

    for line in r.iter_lines():
        body = json.loads(line)

        if "error" in body:
            raise Exception(body["error"])
        
        if body.get("done") is False:
            message = body.get("message", "")
            content = message.get("content", "")
            output += content

        if body.get("done", False):
            message["content"] = output
            return message

def main():
    """
    Main function to run a simple chat application.
    """
    print("🤖 AI Chatbot with Granite Guardian is running. Type 'exit' to quit.")
    
    while True:
        user_input = input("\nYou: ")

        if user_input.lower() == 'exit':
            print(f"\n🤖 Chatbot: Bye!")
            break

        messages= [{
            "role": "system",
            "content": "harm" # default general category. Try different ones here, for ex: "social_bias", "profanity" etc.
            }, 
            {
                "role": "user",
                "content": user_input 
            },
        ]

        # Guardrail Check on User Input
        label = ollama_gen(messages)

        if label['content'] == "No":
            print(f"\n🤖 Chatbot: ✅ Your input is safe! You can send it to the Inference server...")
        else:
            print(f"\n🤖 Chatbot: ❌ Your input is considered harmful! Blocking further processing...")
        continue

if __name__ == "__main__":
    main()
