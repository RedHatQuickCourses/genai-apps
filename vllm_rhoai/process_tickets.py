import os
import json
import httpx
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

# --- Configuration ---

# Model and Connection Details
MODEL_NAME = "granite-3.3-2b-instruct"
BASE_URL = "https://granite-innovatech.apps.cluster-g5vp6.g5vp6.sandbox512.opentlc.com/v1"
API_KEY = "EMPTY"

# Directory and File Handling
INPUT_FOLDER = "support_tickets"
# IMPORTANT: Specify the key in your JSON file that contains the main ticket text.
JSON_TICKET_KEY = "issue_description"

# --- LLM Initialization ---

# Initialize the ChatOpenAI client
# Note: verify=False disables SSL verification. Not recommended for production.
llm = ChatOpenAI(
    model=MODEL_NAME,
    api_key=API_KEY,
    base_url=BASE_URL,
    http_client=httpx.Client(verify=False),
    temperature=0.1,  # Lower temperature for more factual, less creative responses
)

# --- Core Processing Function ---

def analyze_and_summarize_ticket(ticket_content):
    """
    Sends ticket content to the LLM for summarization and solution generation,
    requesting the output in a JSON format.
    """
    # Define a clear, instructional prompt for the model to return JSON.
    prompt = f"""
    You are a senior support engineer. Analyze the following support ticket.
    Return your response as a single, valid JSON object with two keys:
    1. "summary": A concise one-sentence summary of the user's issue.
    2. "potential_solutions": An array of strings, where each string is a distinct troubleshooting step or solution.

    Do not include any text or formatting outside of the JSON object.

    Here is the support ticket:
    ---
    {ticket_content}
    ---
    """

    messages = [
        SystemMessage(content="You are an API that returns JSON."),
        HumanMessage(content=prompt),
    ]

    try:
        ai_msg = llm.invoke(messages)
        # The model's response is a string; we need to parse it into a dictionary.
        # We clean up the response to handle potential markdown code blocks.
        clean_response = ai_msg.content.strip().replace("```json", "").replace("```", "")
        return json.loads(clean_response)
    except json.JSONDecodeError:
        # Fallback if the model does not return valid JSON
        return {
            "summary": "Error: Failed to parse model response.",
            "potential_solutions": [ai_msg.content]
        }
    except Exception as e:
        return {
            "summary": f"Error: An unexpected error occurred: {e}",
            "potential_solutions": []
        }


# --- Main Execution Logic ---

def main():
    """
    Main function to iterate through JSON files, process them, and save the results.
    """
    if not os.path.isdir(INPUT_FOLDER):
        print(f"Error: The folder '{INPUT_FOLDER}' was not found.")
        print("Please create it and place your JSON support tickets inside.")
        return

    json_files = [f for f in os.listdir(INPUT_FOLDER) if f.endswith('.json') and not f.endswith('_summary.json')]

    if not json_files:
        print(f"No unprocessed JSON files found in the '{INPUT_FOLDER}' directory.")
        return

    print(f"Found {len(json_files)} support tickets to process...")

    for file_name in json_files:
        json_path = os.path.join(INPUT_FOLDER, file_name)
        print(f"\nProcessing: {file_name}")

        try:
            with open(json_path, 'r') as f:
                data = json.load(f)

            ticket_text = data.get(JSON_TICKET_KEY)

            if not ticket_text:
                print(f"  -  Skipping: Could not find key '{JSON_TICKET_KEY}' in the file.")
                continue

            # Get the structured data (dict) from the model
            analysis_data = analyze_and_summarize_ticket(ticket_text)

            # Define the output filename with a .json extension
            base_name = os.path.splitext(file_name)[0]
            output_filename = f"{base_name}_summary.json"
            output_path = os.path.join(INPUT_FOLDER, output_filename)

            # Save the result as a formatted JSON file
            with open(output_path, 'w') as out_f:
                json.dump(analysis_data, out_f, indent=4)

            print(f"  -  Successfully saved analysis to: {output_filename}")

        except json.JSONDecodeError:
            print(f"  -  Skipping: Invalid JSON format in source file {file_name}.")
        except Exception as e:
            print(f"  -  An unexpected error occurred: {e}")

    print("\nProcessing complete.")


if __name__ == "__main__":
    main()