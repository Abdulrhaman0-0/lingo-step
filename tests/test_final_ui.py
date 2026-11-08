import unittest
from pathlib import Path
import tempfile
from unittest.mock import Mock
from letterstars.ui.final_ui import ScreenPainter
from letterstars.ui.final_ui import LingoStepApp
from letterstars.domain.models import Attempt
from letterstars.services.feedback import AnswerFeedback
from letterstars.services.lesson import LessonService
from letterstars.infrastructure.student_progress import StudentProgressStore


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
                 "home":{"learn","revision","progress","logout"},
                 "learn":{"listen","speak","prev","next","back"},
                 "revision":{"camera","listen","prev","next","back"},
                 "progress":{"pair","back"},
                 "pairing":{"copy","close"}}
        for screen,required in screens.items():
            _,buttons=ScreenPainter().render(screen,profiles=[{"id":"test123","name":"سلمى"}])
            self.assertTrue(required.issubset({x for x,_ in buttons}),screen)

    def test_logout_closes_camera_and_preserves_saved_child_progress(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = StudentProgressStore(Path(tmp)/"progress.db")
            child = store.create_student("Test Child")
            store.save(Attempt.make("learn", "B", "B", .95, "correct"))
            app = LingoStepApp.__new__(LingoStepApp)
            app.store = store
            app.lesson = LessonService(Mock(), Mock(), store)
            app.lesson.select("B")
            app.name = "Test Child"
            app.mic_busy = False
            app.camera = Mock()
            app.camera_live = True
            app.name_entry = None
            app.feedback = AnswerFeedback()
            app.feedback.answer("try_again")
            app.render = Mock()
            app.action("logout")
            self.assertEqual(app.page, "welcome")
            self.assertEqual(app.name, "")
            self.assertIsNone(store.current_student())
            self.assertFalse(app.camera_live)
            app.camera.close.assert_called_once()
            app.lesson.voice.stop.assert_called_once()
            self.assertEqual(app.feedback.wrong_attempts, 0)
            store.select_student(child)
            self.assertEqual(store.summary()["correct"], 1)


if __name__=="__main__":
    unittest.main()
