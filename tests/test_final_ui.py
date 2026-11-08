import unittest
from pathlib import Path
import tempfile
from unittest.mock import Mock, patch
from letterstars.ui.final_ui import ScreenPainter
from letterstars.ui.final_ui import LingoStepApp
from letterstars.domain.models import Attempt
from letterstars.services.feedback import AnswerFeedback
from letterstars.services.lesson import LessonService
from letterstars.infrastructure.student_progress import StudentProgressStore


class FinalUIRenderTests(unittest.TestCase):
    def test_name_input_keeps_widget_and_focus_when_screen_redraws(self):
        app=LingoStepApp.__new__(LingoStepApp)
        app.page, app.name, app.status = "welcome", "", ""
        app.video, app.camera_live = None, False
        app.name_entry, app._entry_window = None, None
        app.root, app.canvas, app.lesson, app.store, app.image_model = [Mock() for _ in range(5)]
        app.canvas.winfo_width.return_value = 1100
        app.canvas.winfo_height.return_value = 770
        app.canvas.create_window.return_value = 42
        app.store.students.return_value = []
        app.lesson.target = "A"
        app.image_model.ready = False
        with patch("letterstars.ui.final_ui.tk.Entry") as entry, \
             patch("letterstars.ui.final_ui.ImageTk.PhotoImage"):
            entry.return_value.get.return_value = "Sara"
            app.render()
            app.render()
            app.focus_name_entry()
            entry.assert_called_once()
            app.canvas.create_window.assert_called_once()
            entry.return_value.destroy.assert_not_called()
            entry.return_value.focus_set.assert_called_once()
            self.assertEqual(app.name_entry.get(), "Sara")
            self.assertNotIn(("all",), [call.args for call in app.canvas.delete.call_args_list])

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
