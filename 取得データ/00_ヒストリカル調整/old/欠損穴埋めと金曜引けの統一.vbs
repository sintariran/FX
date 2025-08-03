Const filePath = "Z:\00_ヒストリカルデータ\ver2\201905\CSV\EURUSD1440.csv"
Const outPath = "Z:\00_ヒストリカルデータ\ver2\201905\CSV\EURUSD1440_new.csv"

Const dateCol = 0
Const timeCol = 1

Call CutFridayTime

Sub CutFridayTime()
    MsgBox "Start", vbInformation    
    histLst = readCsv(filePath)
    
    Dim newHistLst
    ReDim newHistLst(0)
    newHistLst(0) = histLst(0)
    
    For i = LBound(histLst) + 1 To UBound(histLst)
        If i Mod 1000 = 0 Then
            Call AppendSingleText(outData, CStr(outPath))
            outData = ""
        End If
        deleteFlg = False
        histRowLst = Split(histLst(i), ",")
        If UBound(histRowLst) <= 1 Then Exit For
        
        targetDate = Replace(histRowLst(dateCol), ".", "/")
        targetTime = histRowLst(timeCol)
        targetDateTime = Join(Array(targetDate, " ", targetTime), "")
        targetDateTime = DateAdd("n", 0, targetDateTime)
        WeekNum = Weekday(targetDate)
        
        diffMinute = DateDiff("n", preDateTime, targetDateTime)
        If diffMinute <> 1 Then
            If Not (WeekNum = 1 Or WeekNum = 7) Then
                If Day(preDateTime) = Day(targetDateTime) Then
                    '欠損時刻ぶんのデータを作成する(日付切替なし)
                    missingDateTime = DateAdd("n", 1, preDateTime)
                    missingRowLst = Split(histLst(preIndex), ",")
                    Do While targetDateTime > missingDateTime
                        missingRowLst(timeCol) = FormatDateTime(missingDateTime, vbShortTime)
                        If IsArray(missingLst) Then
                            missingLst = Split(Join(missingLst, vbCrLf) & vbCrLf & Join(missingRowLst, ","), vbCrLf)
                        Else
                            missingLst = Array(Join(missingRowLst, ","))
                        End If
                        missingDateTime = DateAdd("n", 1, missingDateTime)
                    Loop
                Else
                    '欠損時刻ぶんのデータを作成する(日付切替あり)
                    If preDateTime <> "" Then
                        If FormatDateTime(targetDateTime, vbShortTime) <> "00:00" Then
                            missingDateTime = FormatDateTime(targetDateTime, vbShortDate)
                            missingDateTime = DateAdd("n", 0, missingDateTime)
                            missingRowLst = Split(histLst(preIndex), ",")
                            Do While targetDateTime > missingDateTime
                                missingRowLst(dateCol) = histRowLst(dateCol)
                                missingRowLst(timeCol) = FormatDateTime(missingDateTime, vbShortTime)
                                If IsArray(missingLst) Then
                                    missingLst = Split(Join(missingLst, vbCrLf) & vbCrLf & Join(missingRowLst, ","), vbCrLf)
                                Else
                                    missingLst = Array(Join(missingRowLst, ","))
                                End If
                                missingDateTime = DateAdd("n", 1, missingDateTime)
                            Loop
                        End If
                    End If
                End If
            End If
        End If
        
        Select Case WeekNum
        Case 1, 7
            '土日の場合
            deleteFlg = True
        Case 6
            '23時45分以降を抽出
            targetTime = histRowLst(timeCol)
            If Hour(targetTime) = 23 And Minute(targetTime) > 45 Then
                deleteFlg = True
            End If
        End Select
        
        If Not deleteFlg Then
            If outData <> "" Then
                If IsArray(missingLst) Then
                    For j = 0 To UBound(missingLst)
                        outData = outData & vbCrLf & missingLst(j)
                    Next
                    missingLst = ""
                End If
                outData = outData & vbCrLf & histLst(i)
            Else
                outData = histLst(i)
            End If
        End If
        
        preDateTime = targetDateTime
        preIndex = i
    Next

    MsgBox "Finish", vbInformation
End Sub

'***********************************************************
' 機能   : CSV読込処理
' 引数   :
' 戻り値 : なし
' 作成者  : 佐藤
'***********************************************************
Function readCsv(File_Target)
    With CreateObject("Scripting.FileSystemObject")
        Set fp = .OpenTextFile(File_Target, 1, False)
        If fp.AtEndOfStream = True Then
        Else
            Lines = fp.ReadAll
        End If
        fp.Close
    End With

    Dim str_Strings
    str_Strings = Split(Lines, vbCrLf)

    readCsv = str_Strings

End Function

'***********************************************************
' 機能   : ファイル保存処理
' 引数   :  strText:変数
'           filePath:ファイル保存場所
' 戻り値?､ : なし
' 作成者  : 野島
'***********************************************************
Sub AppendSingleText(strText, filePath)
    Set objFso = CreateObject("Scripting.FileSystemObject")
    strParent = objFso.GetParentFolderName(filePath)
    Call CreateDir(strParent)
            
	Set objFile = objFso.OpenTextFile(filePath, 8, True)

	If Err.Number > 0 Then
	    WScript.Echo "Open Error"
	Else
	    objFile.WriteLine strText
	End If

	objFile.Close
	Set objFile = Nothing
	Set objFso = Nothing
End Sub

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
