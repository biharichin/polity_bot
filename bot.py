import os
import json
import telegram
import time
from telegram.error import Unauthorized

def get_correct_option_id(options, answer):
    """Converts the answer (e.g., 'A') to a zero-based index."""
    return list(options.keys()).index(answer)

def load_progress(state_file):
    if os.path.exists(state_file):
        with open(state_file, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_progress(state_file, progress):
    with open(state_file, 'w') as f:
        json.dump(progress, f, indent=4)

def main():
    """
    This is the main function that sends the MCQ questions.
    """
    try:
        bot_token = os.environ['TELEGRAM_TOKEN']
        chat_ids = os.environ['TELEGRAM_CHAT_IDS'].split(',')
    except KeyError:
        print("Error: Please set the TELEGRAM_TOKEN and TELEGRAM_CHAT_IDS environment variables.")
        return

    bot = telegram.Bot(token=bot_token)
    
    questions_file = 'mcq_questions.json'
    state_file = 'user_progress.json'

    with open(questions_file, 'r', encoding='utf-8') as f:
        questions = json.load(f)

    progress = load_progress(state_file)

    for chat_id in chat_ids:
        last_index = progress.get(chat_id, 0)

        if last_index >= len(questions):
            print(f"All questions sent for chat ID {chat_id}.")
            continue

        start_index = last_index
        end_index = min(start_index + 20, len(questions))
        
        questions_to_send = questions[start_index:end_index]

        try:
            for question_data in questions_to_send:
                options = list(question_data['options'].values())
                correct_option_id = get_correct_option_id(question_data['options'], question_data['answer'])
                
                bot.send_poll(
                    chat_id=chat_id,
                    question=f"Q{question_data['id']}: {question_data['question']}",
                    options=options,
                    type=telegram.Poll.QUIZ,
                    correct_option_id=correct_option_id,
                    is_anonymous=True
                )
                time.sleep(1) # Delay between each poll

            # If all polls are sent successfully, update the progress for this user
            progress[chat_id] = end_index

        except Unauthorized:
            print(f"Warning: Bot was blocked by chat ID {chat_id}. Progress not updated.")
            # We don't update the progress, so it will retry from the same point next time
            continue
        
        except Exception as e:
            print(f"An unexpected error occurred for chat ID {chat_id}: {e}")
            continue

    save_progress(state_file, progress)
    print("Script finished.")

if __name__ == '__main__':
    main()