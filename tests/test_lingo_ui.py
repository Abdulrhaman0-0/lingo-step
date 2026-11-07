"""Headless rendering checks (not device/touchscreen certification)."""
import unittest
from letterstars.ui.lingo_ui import Painter

class LingoRenderTests(unittest.TestCase):
    def test_all_screens(self):
        for screen in ('welcome','home','learn','revision','progress'):
            with self.subTest(screen=screen):
                image,hits=Painter().draw(screen,'A','سلمى')
                self.assertEqual(image.size,(1280,900))
                self.assertGreater(len(hits),0)
    def test_learn_controls(self):
        _,hits=Painter().draw('learn')
        self.assertTrue({'back','prev','next','listen','speak'}<=set(k for k,_ in hits))

if __name__=='__main__':unittest.main()
