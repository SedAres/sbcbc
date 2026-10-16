; LocalAcademy 0.2 — optional Windows global media hotkeys
; Run with AutoHotkey v2 while LocalAcademy is open.
; The key mapping is read once from your LocalAcademy preferences at launch.
#Requires AutoHotkey v2.0
#SingleInstance Force

base := "http://127.0.0.1:5000/api/hotkey/"
settingsUrl := "http://127.0.0.1:5000/settings/hotkeys"

try {
    request := ComObject("WinHttp.WinHttpRequest.5.1")
    request.Open("GET", settingsUrl, false)
    request.Send()
    settingsJson := request.ResponseText
    actions := ["play_pause", "rewind_5s", "forward_5s", "prev_file", "next_file", "volume_up", "volume_down", "speed_up", "speed_down", "toggle_subtitles"]
    for action in actions {
        pattern := '"' . action . '"\s*:\s*"num_([0-9])"'
        if RegExMatch(settingsJson, pattern, &match) {
            Hotkey("Numpad" . match[1], Post.Bind(action))
        }
    }
} catch {
    ; If the app is unavailable, no global hotkeys are registered.
}

Post(action, *) {
    global base
    try {
        request := ComObject("WinHttp.WinHttpRequest.5.1")
        request.Open("POST", base . action, false)
        request.Send()
    }
}
