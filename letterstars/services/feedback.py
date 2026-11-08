"""Feedback for evaluated answers in the current letter/activity."""

PHRASES = {
    "correct": "ممتاز",
    "retry": "أحيه! حاول مرة أخرى",
    "retry_again": "يا نهار أسود! حاول مرة أخرى",
}


class AnswerFeedback:
    def __init__(self):
        self.reset()

    def reset(self):
        self.wrong_attempts = 0

    def answer(self, result):
        if result == "correct":
            self.reset()
            key = "correct"
        elif result == "try_again":
            self.wrong_attempts += 1
            key = "retry" if self.wrong_attempts == 1 else "retry_again"
        else:
            return None
        return key, PHRASES[key]
