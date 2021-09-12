import time
import argparse

from zhihulib import *


parser = argparse.ArgumentParser()
parser.add_argument('--question_id', type=int,
                    help='The id of question you want to pack into ebook.')
parser.add_argument('--sort_type', type=str, default='default',
                    help='Value should be either "default" or "updated".')

args = parser.parse_args()


if __name__ == "__main__":
    start_time = time.time()

    question_id = args.question_id
    question = get_question(question_id)
    answer_list = get_answers(question_id, args.sort_type)

    end_time = time.time()
    write_answer_to_file(question, answer_list, end_time-start_time)

    end_time = time.time()
    print(end_time - start_time)
