echo %0
echo off
cd /d %~dp0

set number=284

rem bat�t�@�C������VBScript�����s����T���v��
rem cls

cscript download_new_indicator.vbs %number%

