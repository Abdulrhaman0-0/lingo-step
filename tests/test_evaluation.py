import unittest
from letterstars.domain.models import Prediction
from letterstars.domain.evaluation import decide

class EvaluationTests(unittest.TestCase):
    def test_stable_correct(self):
        self.assertEqual(decide("A",[Prediction("A",0.91)]*5),("correct","A"))
    def test_stable_incorrect(self):
        self.assertEqual(decide("A",[Prediction("B",0.91)]*5),("try_again","B"))
    def test_flicker(self):
        self.assertEqual(decide("A",[Prediction("A",0.91)]*4+[Prediction("B",0.91)])[0],"not_recognized")
    def test_low_confidence(self):
        self.assertEqual(decide("A",[Prediction("A",0.79)]*5)[0],"not_recognized")
    def test_untrusted(self):
        self.assertEqual(decide("A",[Prediction("A",0.99,"mock")]*5)[0],"not_recognized")
    def test_insufficient_frames(self):
        self.assertEqual(decide("A",[Prediction("A",0.99)]*2)[0],"not_recognized")

if __name__=="__main__": unittest.main()
