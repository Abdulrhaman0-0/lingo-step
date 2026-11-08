"""Partial model A..E is usable for trials, not for judging F..Z."""
import unittest
from letterstars.adapters.image_model import validate_labels
from letterstars.services.lesson import LessonService


class ModelLabelTests(unittest.TestCase):
    def test_partial_and_complete(self):
        self.assertEqual(validate_labels(list("ABCDE")), list("ABCDE"))
        self.assertEqual(validate_labels(list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")),list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"))
    def test_wrong_order_invalid(self):
        for labels in ([],["A"],["A","C"],["B","A"],["A","A"],["A","a"]):
            with self.assertRaises(ValueError):
                validate_labels(labels)
    def test_unsupported_target_is_never_inferred_or_saved(self):
        class Img:
            ready=True
            labels=list("ABCDE")
            def predict(self,_):raise AssertionError("Inference should not run")
        class Store:
            def save(self,_):raise AssertionError("Should never save unsupported target")
        class Voice:
            def say_letter(self,_):pass
        s=LessonService(Voice(),Img(),Store())
        s.select("F")
        self.assertEqual(s.check_frame(object()), ("unsupported_letter",None,None))


if __name__=="__main__":
    unittest.main()
