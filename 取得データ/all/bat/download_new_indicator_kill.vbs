Call TaskKill

' -----------------------------------------------------
' 対象のVBSが起動されいているか確認し、検知
' した場合、taskkillする。
' -----------------------------------------------------
Function TaskKill()
    Dim scriptName                  ' 削除対象スクリプト名
    scriptName = "download_new_indicator.vbs"
    Dim computerName                ' コンピュータ名称
    Dim count                       ' 起動プロセス数
    Dim objWMIService               ' WMI
    Dim colItems                    ' wscript検索
    Dim objItem                     ' 検索結果格納
    Dim strcmd                      ' コマンド
    Dim killid(299)                  ' タスクキル対象プロセスID
    Dim objShell                    ' コマンド発行用
    Dim i                           ' カウンタ

    ' 起動しているプロセスを取得
    Set objShell = CreateObject("WScript.Shell")
    computerName = "."
    Set objWMIService = GetObject("winmgmts:" & "{impersonationLevel=impersonate}!\\" & computerName & "\root\cimv2")
    
    ' 上記からwscript.exeを検索・取得
    Set colItems = objWMIService.ExecQuery("Select * from Win32_Process Where Name = 'wscript.exe'")
    
    ' スクリプト名称との一致を検知した場合、PIDを取得
    For Each objItem In colItems
        If InStr(objItem.CommandLine, scriptName) > 0 Then
            killid(count) = objItem.ProcessId
            count = count + 1
        End If
    Next
    
    ' プロセスの同時実行を検知した場合、起動順にタスクキルコマンド発行
    If count > 0 Then
        For i = 0 To count - 1
            strcmd = "taskkill /F /T /PID " & killid(i)
            objShell.Exec (strcmd)
        Next
        
'        ' 最後に自身もキルする
'        strcmd = "taskkill /F /T /PID " & killid(0)
'        objShell.Exec (strcmd)
    End If
End Function