# list_word_fileconverters.py
import win32com.client as win32
word = win32.Dispatch("Word.Application")
for fc in word.FileConverters:
    print(fc.Id, fc.FormatName)
word.Quit()
