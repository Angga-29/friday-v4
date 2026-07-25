' ==============================================================
'   start_windows_silent.vbs — Project Friday v5.0.0
'   Launcher TANPA jendela terminal sama sekali.
'
'   CARA PAKAI:
'     Double-click file ini (atau buat shortcut ke file ini di
'     Desktop / Startup folder Windows untuk auto-start).
'
'   Semua output (status, error) ditulis ke friday.log di folder
'   yang sama, karena tidak ada jendela terminal untuk menampilkannya.
'   UI utama tetap ada di dashboard browser (http://localhost:8765).
' ==============================================================

Set objShell = CreateObject("WScript.Shell")
Set objFSO   = CreateObject("Scripting.FileSystemObject")

strPath = objFSO.GetParentFolderName(WScript.ScriptFullName)
objShell.CurrentDirectory = strPath

' Tandai proses sebagai headless — main.py akan redirect print() ke friday.log
objShell.Environment("Process")("FRIDAY_HEADLESS") = "1"

' Pakai pythonw.exe dari venv kalau ada, kalau tidak pakai yang ada di PATH
venvPythonw = strPath & "\venv\Scripts\pythonw.exe"
If objFSO.FileExists(venvPythonw) Then
    pythonwExe = venvPythonw
Else
    pythonwExe = "pythonw.exe"
End If

mainScript = strPath & "\main.py"

' windowStyle 0 = hidden, waitOnReturn False = jangan blokir script ini
objShell.Run """" & pythonwExe & """ """ & mainScript & """", 0, False
