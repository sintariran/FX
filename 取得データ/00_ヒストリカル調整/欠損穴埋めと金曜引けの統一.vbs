Const dateCol = 0
Const timeCol = 1
Const openCol = 2
Const highCol = 3
Const lowCol = 4
Const closeCol = 5

Call Main

'Sub test()
'    inPath = ActiveSheet.Cells(1, 2)
'    outPath = ActiveSheet.Cells(2, 2)
'
'    Call CutFridayTime(inPath, outPath)
'End Sub

Function Main()

 '�h���b�O�A���h�h���b�v�Ŏ擾�����t�@�C���p�X��ϐ��ɓ����
    Dim GetPathArray
    Set GetPathArray = WScript.Arguments
    
    Dim objFso
    Set objFso = CreateObject("Scripting.FileSystemObject")
 
    MsgBox "Start", vbInformation
 
    '�t�@�C���̐��Ԃ񃋁[�v����
    For Each filePath In GetPathArray
        fileDir = objFso.GetParentFolderName(filePath)
        fileName = objFso.GetBaseName(filePath)
        inPath = fileDir & "\" & fileName & ".csv"
        outPath = fileDir & "\" & fileName & "_adjusted.csv"
        
        Call CutFridayTime(inPath, outPath)
    Next
    
    '�I�u�W�F�N�g�ϐ����N���A
    Set objFso = Nothing
    
    MsgBox "Finish", vbInformation
End Function

Function CutFridayTime(filePath, outPath)
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
        targetDateTime = CDate(targetDateTime)
        WeekNum = Weekday(targetDate)
        
        If histRowLst(openCol) = 0 Or histRowLst(highCol) = 0 Or histRowLst(lowCol) = 0 Or histRowLst(closeCol) = 0 Then
            MsgBox targetDateTime & ": Value is Zero", vbExclamation
        End If

        diffMinute = DateDiff("n", preDateTime, targetDateTime)
        If diffMinute <> 1 Then
            If Not (WeekNum = 1 Or WeekNum = 7) Then
                If Day(preDateTime) = Day(targetDateTime) Then
                    '���������Ԃ�̃f�[�^���쐬����(���t�ؑւȂ�)
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
                    '���������Ԃ�̃f�[�^���쐬����(���t�ؑւ���)
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
            '�y���̏ꍇ
            deleteFlg = True
        Case 6
            '23��45���ȍ~�𒊏o
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
    Call AppendSingleText(outData, CStr(outPath))
End Function

'***********************************************************
' �@�\   : CSV�Ǎ�����
' ����   :
' �߂�l : �Ȃ�
' �쐬��  : ����
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
' �@�\   : �t�@�C���ۑ�����
' ����   :  strText:�ϐ�
'           filePath:�t�@�C���ۑ��ꏊ
' �߂�l?� : �Ȃ�
' �쐬��  : �쓇
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
