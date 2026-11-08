import unittest
from letterstars.adapters.vosk_speech import parse_vosk_result


class VoskParserTests(unittest.TestCase):
    def test_real_transcription(self):
        prediction,text=parse_vosk_result({"text":"bee","result":[{"word":"bee","conf":0.9}]})
        self.assertEqual(prediction.label,"B")
        self.assertAlmostEqual(prediction.confidence,0.9)

    def test_ambiguous_or_unscored(self):
        for value in ({"text":"bee"}, {"text":"a b","result":[{"conf":0.95}]},
                      {"text":""}, {"text":"bee","result":[{"conf":0}]}):
            pred,_=parse_vosk_result(value)
            if value.get("text")=="bee" and value.get("result"):
                self.assertIsNotNone(pred)
                self.assertEqual(pred.confidence,0)
            else:
                self.assertIsNone(pred)

    def test_repeated_same_letter_allowed_but_unknown_and_mixed_rejected(self):
        pred, _ = parse_vosk_result({"text": "bee be", "result": [{"conf": .9}, {"conf": .8}]})
        self.assertEqual(pred.label, "B")
        for text in ("bee dee", "[unk]", "this is a sentence"):
            pred, _ = parse_vosk_result({"text": text, "result": [{"conf": .99}]})
            self.assertIsNone(pred)


if __name__=="__main__":
    unittest.main()
