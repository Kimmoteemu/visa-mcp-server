import os.path
import pandas as pd
import logging

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

# The ID and range of a sample spreadsheet.
SAMPLE_SPREADSHEET_ID = "1VudMmSvYVEliDA1LxJkbg7RXWuqLqMPry0UC2vJdrGo"
SAMPLE_RANGE_NAME = "A2:C"

logging.basicConfig(level=logging.INFO,handlers=[logging.FileHandler("sheets.log")],encoding="utf-8")
def update_questions_from_sheets():
  """Shows basic usage of the Sheets API.
  Prints values from a sample spreadsheet.
  """
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())

  try:
    service = build("sheets", "v4", credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()
    result = (
        sheet.values()
        .get(spreadsheetId=SAMPLE_SPREADSHEET_ID, range=SAMPLE_RANGE_NAME)
        .execute()
    )
    values = result.get("values", [])

    if not values:
      logging.info("No data found.")
      return
    df = pd.DataFrame(values, columns=["question", "answer", "comment"])
    df.to_json('questions.json', orient='records', indent=2)
    logging.info(f"Loaded {len(df)} questions from Google Sheets.")
  except HttpError as err:
    logging.error(err)


if __name__ == "__main__":
  update_questions_from_sheets()