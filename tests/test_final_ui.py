import unittest
from letterstars.ui.final_ui import ScreenPainter


class FinalUIRenderTests(unittest.TestCase):
    def test_all_native_screens_draw_offline(self):
        for screen in ("welcome","home","learn","revision","progress","pairing"):
            with self.subTest(screen=screen):
                im,buttons=ScreenPainter().render(screen,"A","طفل",
                    [{"id":"test123","name":"سلمى"}],
                    {"correct":1,"try_again":0,"learned":1,"total":1,"letters":["A"]})
                self.assertEqual(im.size,(1280,900))
                self.assertGreater(len(buttons),0)

    def test_tappable_functions(self):
        screens={"welcome":{"create","profile:test123"},
                 "home":{"learn","revision","progress"},
                 "learn":{"listen","speak","prev","next","back"},
                 "revision":{"camera","listen","prev","next","back"},
                 "progress":{"pair","back"},
                 "pairing":{"copy","close"}}
        for screen,required in screens.items():
            _,buttons=ScreenPainter().render(screen,profiles=[{"id":"test123","name":"سلمى"}])
            self.assertTrue(required.issubset({x for x,_ in buttons}),screen)


if __name__=="__main__":
    unittest.main()
