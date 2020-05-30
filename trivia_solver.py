import re
import json


class TriviaSolver:
    P_REMOVE_WEIRD_CHARS = re.compile("[^A-Za-z0-9]")

    def __init__(self):
        with open("data/trivia.json") as f:
            self.trivia_list = json.load(f)
            for q in self.trivia_list:
                q["question"] = self.normalize_text(q["question"])

    @staticmethod
    def normalize_text(txt):
        return TriviaSolver.P_REMOVE_WEIRD_CHARS.sub("", txt).lower()

    def solve(self, question, answers):
        question = self.normalize_text(question)
        answers = [self.normalize_text(a) for a in answers]
        for q in self.trivia_list:
            if q["question"] == question:
                correct_answer = self.normalize_text(q["correct_answer"])
                for i, a in enumerate(answers):
                    if a == correct_answer:
                        return i
        return None
