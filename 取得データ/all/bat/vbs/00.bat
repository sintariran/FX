echo %0
echo off
cd /d %~dp0

set number=284

rem batファイルからVBScriptを実行するサンプル
rem cls

cscript download_new_indicator.vbs %number%

