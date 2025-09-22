
import os
import json
import telegram
import time
from telegram.error import Unauthorized

def get_correct_option_id(options, answer):
    """Converts the answer (e.g., 'A') to a zero-based index."""
    return list(options.keys()).index(answer)

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
    state_file = 'last_question_index.txt'

    with open(questions_file, 'r', encoding='utf-8') as f:
        questions = json.load(f)

    last_index = 0
    if os.path.exists(state_file):
        with open(state_file, 'r') as f:
            try:
                last_index = int(f.read().strip())
            except (ValueError, IndexError):
                last_index = 0
    
    if last_index >= len(questions):
        for chat_id in chat_ids:
            try:
                bot.send_message(chat_id=chat_id, text="All questions have been sent. We are done!")
            except Unauthorized:
                print(f"Warning: Bot was blocked by chat ID {chat_id}. Could not send completion message.")
        print("All questions have been sent.")
        return

    start_index = last_index
    end_index = min(start_index + 20, len(questions))
    
    questions_to_send = questions[start_index:end_index]

    new_last_index = last_index

    for i, question_data in enumerate(questions_to_send):
        current_question_index = start_index + i
        poll_sent_to_at_least_one_user = False
        for chat_id in chat_ids:
            try:
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
                poll_sent_to_at_least_one_user = True
            except Unauthorized:
                print(f"Warning: Bot was blocked by chat ID {chat_id}. Skipping this user.")
                continue
            except Exception as e:
                print(f"An unexpected error occurred for chat ID {chat_id} while sending question {question_data['id']}: {e}")
                continue
        
        if poll_sent_to_at_least_one_user:
            new_last_index = current_question_index + 1
            time.sleep(1)
        else:
            print(f"Could not send question {question_data['id']} to any user. Stopping for this run.")
            break

    if new_last_index > last_index:
        with open(state_file, 'w') as f:
            f.write(str(new_last_index))
        print(f"Progress file updated. Next start index will be {new_last_index}.")
    else:
        print("No new questions were sent successfully. Progress file not updated.")

if __name__ == '__main__':
    main()
