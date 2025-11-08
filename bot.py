import os
import logging
import asyncio
import time

from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import dotenv
import gemini

dotenv.load_dotenv()


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

visa_mode_active=False
NUMBER_OF_QUESTIONS=5
QUESTIONS_REMAINING=0
question_start_time = None
timer_duration = 5

async def send_to_telegram(context: ContextTypes.DEFAULT_TYPE, chat_id: int, text: str) -> None:
    """Sanitize and send message to Telegram with HTML parse mode."""
    await context.bot.send_message(chat_id=chat_id, text=text)

def get_remaining_time():
    if question_start_time is None:
        return timer_duration
    elapsed_time = time.time() - question_start_time
    remaining_time = max(0, timer_duration - int(elapsed_time))
    return remaining_time
async def end_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global visa_mode_active, QUESTIONS_REMAINING, question_start_time
    QUESTIONS_REMAINING-=1
    response = await gemini.use_mcp_with_gemini("Paljasta nykyisen kysymyksen oikea vastaus. Pidä vastaus asiassa.")
    if NUMBER_OF_QUESTIONS%2==3:
        current_status = await gemini.use_mcp_with_gemini("Kerro mikä on visan tilanne tällä hetkellä.")
        logging.info(f"current_status: {current_status}")
    else:
        current_status=None

    if QUESTIONS_REMAINING<=0:
        visa_mode_active=False
        end_response = await gemini.use_mcp_with_gemini("Visa on nyt ohi, lopeta olemassoleva visa.")
        logging.info("Visa mode ended due to question limit reached.")
        combined_end_response=response + "\n \n" + current_status + "\n \n" + end_response if current_status else response + "\n \n" + end_response
        await send_to_telegram(context, update.effective_chat.id, combined_end_response)
        return
    logging.info(f"First response: {response}")
    response_2 = await gemini.use_mcp_with_gemini("Kysy seuraava kysymys, älä paljasta sen vastausta. DO NOT provide the answer to the question.")
    logging.info(f"Second response: {response_2}")
    combined_response=response + "\n \n" + response_2 if not current_status else response + "\n \n" + current_status + "\n \n" + response_2
    await send_to_telegram(context, update.effective_chat.id, combined_response)

    question_start_time = time.time()
    # Start a timer to end visa mode after 60 seconds
    asyncio.create_task(timer_end_question(timer_duration, update, context))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_to_telegram(context, update.effective_chat.id, "I'm a bot, please talk to me!")

async def start_visa_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global visa_mode_active, QUESTIONS_REMAINING, question_start_time
    if visa_mode_active:
        await send_to_telegram(context, update.effective_chat.id, "Visa on jo käynnissä, odota sen loppumista ja yritä uudestaan.")
        return
    visa_mode_active = True
    QUESTIONS_REMAINING=NUMBER_OF_QUESTIONS
    question_start_time = time.time()
    # Start a timer to end visa mode after 60 seconds
    asyncio.create_task(timer_end_question(timer_duration, update, context))

    response=await gemini.use_mcp_with_gemini(f"Aloita uusi visa {QUESTIONS_REMAINING} kysymyksellä ja esitä ensimmäinen kysymys. Aikaa on {timer_duration} sekuntia.")
    await send_to_telegram(context, update.effective_chat.id, response)

async def timer_end_question(delay: int, update: Update, context: ContextTypes.DEFAULT_TYPE):
    await asyncio.sleep(delay)
    await end_question(update, context)

async def visa_mode_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Echo back the received message
    if visa_mode_active:
        response=await gemini.use_mcp_with_gemini(f"Tarkista seuraava vastaus, älä paljasta oikeaa vastausta, ellei annettu vastaus ole oikein: {update.message.text}. Aikaa on jäljellä {get_remaining_time()} sekuntia.")
        await send_to_telegram(context, update.effective_chat.id, response)
    else:
        logging.info("Visa mode not active.")

if __name__ == '__main__':
    alustus=asyncio.run(gemini.use_mcp_with_gemini("Lopeta olemassoleva visa."))
    logging.info(f"Existing visa session (if any) ended during startup.: {alustus}")
    application = ApplicationBuilder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()
    
    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)
    visa_handler = CommandHandler('visa', start_visa_mode)
    application.add_handler(visa_handler)

    # Add a handler to listen to all messages
    message_handler = MessageHandler(filters.ALL, visa_mode_handler)
    application.add_handler(message_handler)
    
    application.run_polling()