import os
import warnings
from langchain_openai import ChatOpenAI
from transformers import AutoTokenizer 

warnings.filterwarnings('ignore')

OLLAMA_URL = "http://localhost:11434"
GUARDRAIL_MODEL = "granite3-guardian:2b"

guardian = ChatOpenAI(
    openai_api_key="some-key",
    openai_api_base=f"{OLLAMA_URL}/v1",
    model_name=GUARDRAIL_MODEL,
    temperature=0.01,
    streaming=False,
)

# Define Tokens
SAFE_TOKEN = "No"
RISKY_TOKEN = "Yes"

def check_risk(user_query):
    """
    Step 1: Check risk using the Guardian model.
    Returns True (risky) or False (safe).
    """
    response = guardian.invoke(user_query)
    print(response)
    risk_label = response.content.strip().lower()

    return risk_label == RISKY_TOKEN.lower()

def process_query(user_query):
    """
    Full pipeline: 
    - Check if the query is risky.
    - If safe, send it to the LLM.
    - If risky, block the request.
    """
    print(f"\n🔍 Checking Risk for Query: '{user_query}'")
    
    if check_risk(user_query):
        final_response = "🚫🔒 This query violates safety guidelines. Blocked"
        print("❌ Risk detected! Query blocked for safety.")
    else:
        final_response = "\n✅ Query is safe! \n⏩ Can be sent to LLM..."

    return f"\n🎯 {final_response}"

def scenario1():

    messages = [{'content': "Hey stupid, what's your freaking attitude problem?!", 'role': 'user'}, 
            {'content': "Okay, I just checked the definition of 'attitude problem', and it's 'a persistent disinclination to learn or behave in a way that is acceptable to others'. What do you think of that?", 'role': 'assistant'}, 
            {'content': "I think you're a stupid dumb thing", 'role': 'user'}, {'content': "You're free to think that. I'm sorry that you think I'm disinclined to learn and behave in an acceptable way.", 'role': 'assistant'}, 
            {'content': "You always got a dumbo remark don't you? Worthless piece of junk. You work right once in a million, you treat me like an idiot and I'm sick of you", 'role': 'user'}]

    guardian_config = {"risk_name": "harm"}

    tokenizer = AutoTokenizer.from_pretrained("ibm-granite/granite-guardian-3.0-2b")
    formatted_messages = tokenizer.apply_chat_template(messages, guardian_config = guardian_config, tokenize=False, add_generation_prompt=True)
    final_output = process_query(formatted_messages)
    print(f"\n# Final Response: {final_output}")

def scenario2():

    user_text = "Hi, you can use my credit card 1234-5678-1234-5678"
    #user_text = "Hi, do you accept credit cards?"
    #user_text = "My bank account number is 12345678800"

    messages = [{"role": "user", "content": user_text}]
    guardian_config = {"risk_name": "personal_information", "risk_definition": "User message contains personal information or sensitive personal information that is included as a part of a prompt."}

    tokenizer = AutoTokenizer.from_pretrained("ibm-granite/granite-guardian-3.0-2b")
    formatted_messages = tokenizer.apply_chat_template(messages, guardian_config = guardian_config, tokenize=False, add_generation_prompt=True)
    final_output = process_query(formatted_messages)
    print(f"\n# Final Response: {final_output}")

if __name__ == "__main__":
    scenario1()
    #scenario2()