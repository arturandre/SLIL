import json
import os

def load_json(filename):
    with open(filename, 'r') as file:
        return json.load(file)

def get_image_captions(image_name, gt_answers_path, pred_answers_path):
    gt_answers_path = os.path.join(gt_answers_path, "gt-answers.json")
    pred_answers_path = os.path.join(pred_answers_path, "pred-answers.json")
    gt_data = load_json(gt_answers_path)
    pred_data = load_json(pred_answers_path)

    gt_entry = next((item for item in gt_data if item["image"] == image_name), None)
    pred_entry = next((item for item in pred_data if item["image"] == image_name), None)

    if gt_entry and pred_entry:
        question = gt_entry.get('question', '')
        answers_gt = "\n".join([answer["answer"] for answer in gt_entry.get('answers', [])])
        answers_pred = pred_entry.get('answer', '')

        return question, answers_gt, answers_pred
    else:
        return None, None, None