
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
    print("Starting the bot...")
    try:
        bot_token = os.environ['TELEGRAM_TOKEN']
        chat_ids = os.environ['TELEGRAM_CHAT_IDS'].split(',')
    except KeyError:
        print("Error: Please set the TELEGRAM_TOKEN and TELEGRAM_CHAT_IDS environment variables.")
        return

    bot = telegram.Bot(token=bot_token)
    
    questions_file = 'mcq_questions.json'
    state_file = 'last_question_index.txt'

    print(f"Reading questions from {questions_file}...")
    with open(questions_file, 'r', encoding='utf-8') as f:
        questions = json.load(f)
    print(f"Loaded {len(questions)} questions.")

    last_index = 0
    print(f"Checking for state file: {state_file}")
    if os.path.exists(state_file):
        with open(state_file, 'r') as f:
            try:
                content = f.read().strip()
                print(f"State file content: '{content}'")
                last_index = int(content)
            except (ValueError, IndexError):
                print("State file is empty or contains invalid data, starting from 0.")
                last_index = 0
    else:
        print("State file not found, starting from 0.")
    
    print(f"Last question index from file: {last_index}")

    if last_index >= len(questions):
        print("All questions have been sent.")
        for chat_id in chat_ids:
            try:
                bot.send_message(chat_id=chat_id, text="All questions have been sent. We are done!")
            except Unauthorized:
                print(f"Warning: Bot was blocked by chat ID {chat_id}. Could not send completion message.")
        return

    start_index = last_index
    end_index = min(start_index + 20, len(questions))
    
    print(f"Preparing to send questions from index {start_index} to {end_index - 1}")
    questions_to_send = questions[start_index:end_index]

    new_last_index = last_index

    for i, question_data in enumerate(questions_to_send):
        current_question_index = start_index + i
        print(f"Processing question {question_data['id']} (index {current_question_index})")
        poll_sent_to_at_least_one_user = False
        for chat_id in chat_ids:
            try:
                options = list(question_data['options'].values())
                correct_option_id = get_correct_option_id(question_data['options'], question_data['answer'])
                
                print(f"Sending question {question_data['id']} to chat ID {chat_id}...")
                bot.send_poll(
                    chat_id=chat_id,
                    question=f"Q{question_data['id']}: {question_data['question']}",
                    options=options,
                    type=telegram.Poll.QUIZ,
                    correct_option_id=correct_option_id,
                    is_anonymous=True
                )
                print(f"Successfully sent question {question_data['id']} to chat ID {chat_id}")
                poll_sent_to_at_least_one_user = True
            except Unauthorized:
                print(f"Warning: Bot was blocked by chat ID {chat_id}. Skipping this user.")
                continue
            except Exception as e:
                print(f"An unexpected error occurred for chat ID {chat_id} while sending question {question_data['id']}: {e}")
                continue
        
        if poll_sent_to_at_least_one_user:
            new_last_index = current_question_index + 1
            print(f"Question {question_data['id']} sent to at least one user. New last index will be {new_last_index}")
            time.sleep(1)
        else:
            print(f"Could not send question {question_data['id']} to any user. Stopping for this run.")
            break

    print(f"Finished sending questions for this run. Last index was {last_index}, new last index is {new_last_index}")

    if new_last_index > last_index:
        print(f"Updating state file '{state_file}' with new index: {new_last_index}")
        try:
            with open(state_file, 'w') as f:
                f.write(str(new_last_index))
            print("State file updated successfully.")
        except Exception as e:
            print(f"Error writing to state file: {e}")
    else:
        print("No new questions were sent successfully. Progress file not updated.")
    
    print("Bot run finished.")

if __name__ == '__main__':
    main()
