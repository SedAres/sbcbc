; LocalAcademy Hotkeys - AutoHotkey v2
#Requires AutoHotkey v2.0
#SingleInstance Force

base := "http://127.0.0.1:5000/api/hotkey"

Numpad5:: Post("play_pause")
Numpad4:: Post("rewind_5s")
Numpad6:: Post("forward_5s")
Numpad1:: Post("prev_file")
Numpad3:: Post("next_file")
Numpad8:: Post("volume_up")
Numpad2:: Post("volume_down")
Numpad9:: Post("speed_up")
Numpad7:: Post("speed_down")
Numpad0:: Post("toggle_subtitles")
^+p:: Post("play_pause")

Post(action) {
    try {
        whr := ComObject("WinHttp.WinHttpRequest.5.1")
        whr.Open("POST", base . "/" . action)
        whr.Send()
        whr.WaitForResponse()
    }
}
