import json
import os

def load_json(filename):
    with open(filename, 'r') as file:
        return json.load(file)

def get_image_captions(image_name, gt_answers_path, pred_answers_path):
    gt_answers_path = os.path.join(gt_answers_path, "gt-answers.json")
    pred_answers_path = os.path.join(pred_answers_path, "pred-answers.json")
    questions = []
    answers_gt = []
    answers_pred = []
    if os.path.exists(gt_answers_path):
        gt_data = load_json(gt_answers_path)
        gt_entries = list(item for item in gt_data if item["image"] == image_name)
        for gt_entry in gt_entries:
            question = gt_entry.get('question', '')
            answers = gt_entry.get('answers', [])
            if isinstance(answers, list) > 0:
                print(answers)
                answer_gt = "\n".join([answer["answer"] for answer in answers])
            else:
                answer_gt = answers
            questions.append(question)
            answers_gt.append(answer_gt)

    if os.path.exists(pred_answers_path):
        pred_data = load_json(pred_answers_path)
        pred_entry = [item for item in pred_data if item["image"] == image_name][0]
        answer_pred = pred_entry.get('answer', '')
        answers_pred.append(answer_pred)


    return questions, answers_gt, answers_pred
