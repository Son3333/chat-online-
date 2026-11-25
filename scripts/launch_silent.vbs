Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
rootDir = fso.GetParentFolderName(scriptDir)
batFile = rootDir & "\CHAY_UNG_DUNG.bat"
shell.CurrentDirectory = rootDir
shell.Run Chr(34) & batFile & Chr(34), 0, False
