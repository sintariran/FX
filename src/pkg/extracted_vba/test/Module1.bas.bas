Attribute VB_Name = "Module1"
'MT4からDLしたNESLファイルの入った日付フォルダがおいてあるフォルダパスを指定
Const targetDir = "C:\VBS_日足用\all\bat\vbs"
'同時に処理するプロセス数の最大値
Const maxExecCount = 20
'initial_settin_list_osのパス
Const confPath = "C:\VBS_日足用\all\bat\vbs\initial_setting_list_os_full.csv"
'initial_settin_list_osの列情報
Const noCol = 0
Const kaisouCol = 13
Const onoffCol = 15

'Call CombineNesl

Sub CombineNesl()
    kaisouNum = 1
    maxKaisou = 1
    Set objfso = CreateObject("Scripting.FileSystemObject")
    Set objShell = CreateObject("WScript.Shell")
    'CurDir = objShell.CurrentDirectory
    finishFlgDir = CurDir & "\finish"
    If Not objfso.FolderExists(finishFlgDir) Then
        objfso.CreateFolder (finishFlgDir)
    End If
    confDir = objfso.GetParentFolderName(confPath)
    
    confLst = readCsv(confPath)
    confHeader = confLst(0)


    Do While kaisouNum <= maxKaisou
        For confRow = 1 To UBound(confLst)
            If confLst(confRow) = "" Then Exit For
            confRowLst = Split(confLst(confRow), ",")
            If confRowLst(kaisouCol) <> "" Then
                            
                If CInt(confRowLst(kaisouCol)) = kaisouNum Then
                    If confRowLst(onoffCol) = "1" Then
                        Do While 1
                            'bat実行済みの数 - 出力済みファイルの数 = 現在処理中の数 >= 処理の最大数よりも大きい場合には待ち
                            finishCount = finishFlgCount(finishFlgDir)
                            If (execBatCount - finishCount) <= maxExecCount Then
                                eachConfLst = Array(confHeader, confLst(confRow))
                                eachConfPath = confDir & "\initial_setting_list_os_" & confRow & ".csv"
                                Call OutputArray1D(eachConfLst, eachConfPath)
            
                                batName = "combine" & "_" & FolderName & "_" & confRow & ".bat"
                                batPath = CurDir & "\bat\" & batName
                                commandStr1 = "cd /d " & targetDir
                                commandStr2 = "download_new_indicator.vbs " & "_" & confRow
                                commandStr3 = "cd /d %~dp0"
                                commandStr4 = "type nul > " & finishFlgDir & "\finish" & execBatCount & ".csv"
                                Call OutputArray1D(Array(commandStr1, commandStr2, commandStr3, commandStr4), batPath)
                                Call ExecCmd(batPath)
                                execBatCount = execBatCount + 1
                                Exit Do
                            Else
                                Application.Wait [Now()] + 500 / 86400000
                                'Wscript.Sleep 500
                            End If
                        Loop
                    End If
                Else
                    If CInt(confRowLst(kaisouCol)) > maxKaisou Then
                        maxKaisou = CInt(confRowLst(kaisouCol))
                    End If
                End If
            End If
       Next
       
       '次の階層を探索
       kaisouNum = kaisouNum + 1
    Loop
    
    MsgBox "Finish", vbInformation
    objfso.DeleteFolder CurDir & "\bat"
    objfso.DeleteFolder finishFlgDir
End Sub

Function finishFlgCount(finishFlgDir)
    Set objfso = CreateObject("Scripting.FileSystemObject")
    If objfso.FolderExists(finishFlgDir) Then
        finishCount = objfso.GetFolder(finishFlgDir).Files.Count
    End If
    
    finishFlgCount = finishCount
End Function

Function ExecCmd(commandStr)
    Dim oShell
    Set oShell = CreateObject("WSCript.shell")
    oShell.Run commandStr
    Set oShell = Nothing
End Function

'***********************************************************
' 機能   : CSV読込処理
' 引数   :
' 戻り値 : なし
' 作成者  : 佐藤
'***********************************************************
Function readCsv(File_Target)
    On Error Resume Next
    With CreateObject("Scripting.FileSystemObject")
        Set fp = .OpenTextFile(File_Target, 1, False)
        
        If Err.Number = 0 Then
            If fp.AtEndOfStream = True Then
            Else
                Lines = fp.ReadAll
            End If
            fp.Close
        Else
            MsgBox "ファイル読込エラー" & vbCrLf & File_Target, vbCritical
            Wscript.Quit 10
        End If
    End With

    Dim str_Strings
    str_Strings = Split(Lines, vbCrLf)

    readCsv = str_Strings

End Function


'***********************************************************
' 機能   : ファイル保存処理
' 引数   :  ArrayData:配列変数
'           filePath:ファイル保存場所
' 戻り値?､ : なし
' 作成者  : 野島
'***********************************************************
Function OutputArray1D(ArrayData, filePath)
    Set objFS = CreateObject("Scripting.FileSystemObject")
    strParent = objFS.GetParentFolderName(filePath)
    Call CreateDir(strParent)
              
    Dim fso
    Set fso = CreateObject("Scripting.FileSystemObject")
        
    Dim outputFile
    Set outputFile = fso.OpenTextFile(filePath, 2, True)
        
    maxRowIndex = UBound(ArrayData, 1)
        
    Dim outlst()
    ReDim outlst(0)
    
    For i = LBound(ArrayData) To UBound(ArrayData)
        If ArrayData(i) <> "" Then
    Dim size: size = UBound(outlst)
        If outlst(size) <> "" Then
            ReDim Preserve outlst(size + 1)
        End If
        If UBound(outlst) = 0 Then
            outlst(size) = ArrayData(i)
        Else
            outlst(size + 1) = ArrayData(i)
        End If
    End If
    Next
    
    outText = Join(outlst, vbCrLf)
    outputFile.Write (outText)
    outputFile.Write (vbCrLf)
    
    ' バッファを Flush してファイルを閉じる
    outputFile.Close
    Set fso = Nothing
End Function

Sub CreateDir(Path)
 
   Dim objFS
   Dim strParent
 
   Set objFS = CreateObject("Scripting.FileSystemObject")
   strParent = objFS.GetParentFolderName(Path)
 
   If Not objFS.FolderExists(strParent) Then
      CreateDir (strParent)
   End If
    
   If Not objFS.FolderExists(Path) Then
      objFS.CreateFolder (Path)
   End If
 
   Set objFS = Nothing
End Sub

' IE の初期化
Sub initializeIe()
  Set ie = CreateObject("InternetExplorer.Application")
  With ie
    .Navigate ("about:blank")
    .Toolbar = False
    .StatusBar = False
    ' 幅・高さの設定
    .Width = 300
    .Height = 200
    ' 画面右上に配置する。"parentWindow.screen" はパスカルケースで書くと認識されない
    .Top = 0
    .Left = .Document.parentWindow.screen.Width - 300
    .Document.Charset = "UTF-8"
    .Visible = True
    .Document.Title = "スクリプト実行中"
  End With
End Sub

' メッセージを IE に追記する
'
' 引数のメッセージを IE の最終行に追記する。
' 最終行が表示されるようにスクロール位置を最下部に設定する。
Sub updateMsg(value)
  With ie
    .Document.Body.innerHTML = .Document.Body.innerHTML & value & "<br>"
    .Document.Script.setTimeout "javascript:scrollTo(0," & .Document.Body.ScrollHeight & ");", 0
  End With
End Sub

' IE を終了する
Sub closeIe()
  ie.Quit
  Set ie = Nothing
End Sub



