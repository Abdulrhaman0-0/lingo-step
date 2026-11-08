"""Exercise dialog lifecycle without relying on a platform Configure event."""
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from letterstars.ui.final_ui import LingoStepApp, ScreenPainter, W, H


class PairingDialogTests(unittest.TestCase):
    def open_dialog(self):
        app = LingoStepApp.__new__(LingoStepApp)
        app.root = Mock()
        window, canvas = Mock(), Mock()
        canvas.winfo_width.return_value = 800
        canvas.winfo_height.return_value = 563
        visible = {"value": False}
        window.wait_visibility.side_effect = lambda: visible.update(value=True)

        def grab():
            if not visible["value"]:
                raise RuntimeError("grab failed: window not viewable")
            self.assertTrue(canvas.create_image.called,
                            "The dialog must already have content before becoming modal")

        window.grab_set.side_effect = grab
        with patch("letterstars.ui.final_ui.tk.Toplevel", return_value=window), \
             patch("letterstars.ui.final_ui.tk.Canvas", return_value=canvas), \
             patch("letterstars.ui.final_ui.ImageTk.PhotoImage"):
            # No Configure event is fired by these mocks.
            app.pairing_dialog("Demo-CaseSensitive_Code-1234")
        click = next(call.args[1] for call in canvas.bind.call_args_list
                     if call.args[0] == "<Button-1>")
        return app, window, canvas, click

    def test_initial_content_drawn_after_visibility_without_configure_event(self):
        _, window, canvas, _ = self.open_dialog()
        window.wait_visibility.assert_called_once()
        window.grab_set.assert_called_once()
        canvas.create_image.assert_called_once()

    def test_copy_keeps_exact_code_and_close_button_works(self):
        app, window, canvas, click = self.open_dialog()
        _, targets = ScreenPainter().render("pairing", pair_code="Demo-CaseSensitive_Code-1234")
        scale = min(800/W, 563/H)
        ox, oy = (800-int(W*scale))//2, (563-int(H*scale))//2
        with patch("letterstars.ui.final_ui.ImageTk.PhotoImage"):
            for action in ("copy", "close"):
                x1,y1,x2,y2 = next(bounds for name,bounds in targets if name == action)
                click(SimpleNamespace(x=ox+(x1+x2)/2*scale,
                                      y=oy+(y1+y2)/2*scale))
        app.root.clipboard_append.assert_called_once_with("Demo-CaseSensitive_Code-1234")
        window.destroy.assert_called_once()
