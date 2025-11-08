"""
FastMCP quickstart example.

cd to the `examples/snippets/clients` directory and run:
    uv run server fastmcp_quickstart stdio
"""

from mcp.server.fastmcp import FastMCP
import os
import json
from sheets import update_questions_from_sheets

STATE_FILE = "visa_state.json"
visa_questions, visa_active, current_question, current_question_number = [], False, {"question": "", "answer": ""}, 1
def load_state():
    """Load the state from the JSON file."""
    global visa_questions, visa_active, current_question, current_question_number
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            state = json.load(f)
            visa_questions = state.get("visa_questions", [])
            visa_active = state.get("visa_active", False)
            current_question = state.get("current_question", {"question": "", "answer": ""})
            current_question_number = state.get("current_question_number", 1)
    else:
        visa_questions = []
        visa_active = False
        current_question = {"question": "", "answer": ""}
        current_question_number = 1
    update_questions_from_sheets()

def save_state():
    """Save the current state to the JSON file."""
    with open(STATE_FILE, "w") as f:
        json.dump({
            "visa_questions": visa_questions,
            "visa_active": visa_active,
            "current_question": current_question,
            "current_question_number": current_question_number
        }, f)


# Create an MCP server
mcp = FastMCP("visa-mcp-server-tool", "A tool server for teekkari visa-related questions.")
update_questions_from_sheets()
visa_questions = []
visa_active = False
current_question = {"question": "", "answer": ""}

@mcp.tool()
def load_faqs() -> list[dict]:
    """Load all questions and answers from a JSON file"""
    import json
    with open('questions.json', 'r') as f:
        faqs = json.load(f)
    return faqs

@mcp.tool()
def get_random_faq() -> dict:
    """Get a random question and answer from the FAQs"""
    import json
    import random
    with open('questions.json', 'r') as f:
        faqs = json.load(f)
    return random.choice(faqs)

@mcp.tool()
def start_new_visa(number_of_questions: int) -> dict:
    """Aloita uusi visa ja palauta ensimmäinen kysymys"""
    import random
    with open('questions.json', 'r') as f:
        faqs = json.load(f)
    global visa_questions, visa_active, current_question, current_question_number
    visa_questions = random.sample(faqs, k=number_of_questions)
    visa_active = True
    current_question = visa_questions.pop(0)
    current_question_number = 1
    save_state()  # Save state after starting the visa
    response = {"message": f"Visa started with {number_of_questions} questions. Use get_next_question to get more questions.",
            "first_question": current_question, "question_number": current_question_number}
    return response

@mcp.tool()
def get_current_question() -> dict:
    """
    Get the current question and answer in the active visa session.

    This tool returns the current question and its answer for the ongoing visa session.
    If no session is active, returns the last loaded question or an empty dict.

    Returns:
        dict: {"question": str, "answer": str, "question_number": int}

    Usage:
        Use this tool to retrieve the answer for the current question to check user responses.

        Käytä tätä kun halutaan tarkistaa vastauksia.
    """
    load_state()
    global current_question
    return {**current_question, "question_number": current_question_number}

@mcp.tool()
def get_visa_status() -> dict:
    """Get the current status of the visa session"""
    load_state()
    global visa_active, visa_questions
    return {
        "visa_active": visa_active,
        "remaining_questions": len(visa_questions),
        "question_number": current_question_number
    }

@mcp.tool()
def get_next_question() -> dict:
    """
    Retrieve the next question in the active visa session.

    This tool advances the visa session by popping the next question from the queue.
    If no questions remain, the visa session is ended and a message is returned.

    Returns:
        dict: {"question": str, "question_number": int} for the next question,
              or {"message": str} if the session has ended.

    Usage:
        Use this tool to get the next question and replace the active question.
        Typically called when the user explicitly asks for it. Does not provide the answer.
    """
    # Load state at the start of the application
    load_state()
    global visa_questions, current_question, current_question_number
    if len(visa_questions) == 0:
        return end_visa()
    current_question = visa_questions.pop(0)
    current_question_number += 1
    save_state()  # Save state after getting the next question
    return {"question": current_question["question"], "question_number": current_question_number}

@mcp.tool()
def end_visa() -> dict:
    """End the visa session"""
    global visa_active
    visa_active = False
    save_state()  # Save state after ending the visa
    return {"message": "Visa session ended. "}


# my_server.py (at the end of the file)

if __name__ == "__main__":
    # print("\n--- Starting FastMCP Server via __main__ ---")
    # This starts the server, typically using the stdio transport by default
    mcp.run()
    # print("--- Server Stopped ---\n")