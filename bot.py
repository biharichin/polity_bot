import os
import json
import telegram
import time

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
            except ValueError:
                last_index = 0

    if last_index >= len(questions):
        for chat_id in chat_ids:
            bot.send_message(chat_id=chat_id, text="All questions have been sent. We are done!")
        return

    start_index = last_index
    end_index = min(start_index + 20, len(questions))
    
    questions_to_send = questions[start_index:end_index]

    for chat_id in chat_ids:
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
            # Add a small delay between questions to avoid hitting rate limits
            time.sleep(1)

    with open(state_file, 'w') as f:
        f.write(str(end_index))

if __name__ == '__main__':
    main()