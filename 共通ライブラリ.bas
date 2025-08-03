Attribute VB_Name = "���ʃ��C�u����"
Public Const libraryVersion = "2.0"

Private Type GUID
 Data1 As Long
 Data2 As Integer
 Data3 As Integer
 Data4(7) As Byte
End Type

'Private Declare Function CoCreateGuid Lib "OLE32.DLL" (pGuid As GUID) As Long
Public mileStoneTime As Double

Function combineCondition(arrayLst As Variant, targetRow, startCol)
    For i = 1 To stateMaxCondition
        conName = arrayLst(targetRow, startCol + 3 * (i - 1) + conNameCol)
        If conName = "" Then Exit For
        conTarget = arrayLst(targetRow, startCol + 3 * (i - 1) + conTargetCol)
        conState = arrayLst(targetRow, startCol + 3 * (i - 1) + conStateCol)
        
        combineTarget = targetCode & conTarget & "|"
        combineCondition = conName & "^" & conState & "|"
    Next i
    
    combineTarget = Left(combineTarget, Len(combineTarget) - 1)
    combineCondition = Left(combineCondition, Len(combineCondition) - 1)
    
    combineCondition = combineTarget & "\" & combineCondition
End Function

'***********************************************************
' �@�\   :�@�o�u���\�[�g2�����z��
' �ړI   :  �z�����ёւ���
' ����   :  �\�[�g�����z��
' �߂�l :  �Ȃ�
' �쐬��  : �쓇
'***********************************************************
Sub BubbleSortAsc2(ByRef argAry As Variant, ByVal keyPos As Long)
    Dim vSwap
    Dim i As Integer
    Dim j As Integer
    Dim k As Integer
    For i = LBound(argAry, 1) To UBound(argAry, 1)
        For j = UBound(argAry, 1) To i Step -1
            If argAry(i, keyPos) > argAry(j, keyPos) Then
                For k = LBound(argAry, 2) To UBound(argAry, 2)
                    vSwap = argAry(i, k)
                    argAry(i, k) = argAry(j, k)
                    argAry(j, k) = vSwap
                Next
            End If
        Next j
    Next i
End Sub

Sub BubbleSortDisc2(ByRef argAry As Variant, ByVal keyPos As Long)
    Dim vSwap
    Dim i As Integer
    Dim j As Integer
    Dim k As Integer
    For i = LBound(argAry, 1) To UBound(argAry, 1)
        For j = UBound(argAry, 1) To i Step -1
            If argAry(i, keyPos) < argAry(j, keyPos) Then
                For k = LBound(argAry, 2) To UBound(argAry, 2)
                    vSwap = argAry(i, k)
                    argAry(i, k) = argAry(j, k)
                    argAry(j, k) = vSwap
                Next
            End If
        Next j
    Next i
End Sub

'�N�C�b�N�\�[�g
Sub QuickSort(a_ar, Optional iFirst As Long = 0, Optional iLast As Long = -1)
    Dim iLeft                   As Long      '// �����[�v�J�E���^
    Dim iRight                  As Long      '// �E���[�v�J�E���^
    Dim sMedian                                 '// �����l
    Dim tmp                                     '// �z��ړ��p�o�b�t�@
    
    '// �\�[�g�I���ʒu�ȗ����͔z��v�f����ݒ�
    If (iLast = -1) Then
        iLast = UBound(a_ar)
    End If
    
    '// �����l���擾
    sMedian = a_ar(Fix((iFirst + iLast) / 2))
    
    iLeft = iFirst
    iRight = iLast
    
    Do
        '// �����l�̍��������[�v
        Do
            '// �z��̍������璆���l���傫���l��T��
            If (a_ar(iLeft) >= sMedian) Then
                Exit Do
            End If
            
            '// �������P�E�ɂ��炷
            iLeft = iLeft + 1
        Loop
        
        '// �����l�̉E�������[�v
        Do
            '// �z��̉E�����璆���l���傫���l��T��
            If (sMedian >= a_ar(iRight)) Then
                Exit Do
            End If
            
            '// �E�����P���ɂ��炷
            iRight = iRight - 1
        Loop
        
        '// �����̕����傫����΂����ŏ����I��
        If (iLeft >= iRight) Then
            Exit Do
        End If
        
        '// �E���̕����傫���ꍇ�́A���E�����ւ���
        tmp = a_ar(iLeft)
        a_ar(iLeft) = a_ar(iRight)
        a_ar(iRight) = tmp
        
        '// �������P�E�ɂ��炷
        iLeft = iLeft + 1
        '// �E�����P���ɂ��炷
        iRight = iRight - 1
    Loop
    
    '// �����l�̍������ċA�ŃN�C�b�N�\�[�g
    If (iFirst < iLeft - 1) Then
        Call QuickSort(a_ar, iFirst, iLeft - 1)
    End If
    
    '// �����l�̉E�����ċA�ŃN�C�b�N�\�[�g
    If (iRight + 1 < iLast) Then
        Call QuickSort(a_ar, iRight + 1, iLast)
    End If
End Sub

'***********************************************************
' �@�\   :�@�N�C�b�N�\�[�g2�����z��
' �ړI   :  �z�����ёւ���
' ����   :  �\�[�g�����z��
' �߂�l :  �Ȃ�
' �쐬��  : �쓇
'***********************************************************
Sub QuickSort2(ByRef argAry As Variant, ByVal lngMin As Long, ByVal lngMax As Long, ByVal keyPos As Long)
    Dim i As Long
    Dim j As Long
    Dim k As Long
    Dim vBase As Variant
    Dim vSwap As Variant
    vBase = argAry(Int((lngMin + lngMax) / 2), keyPos)
    i = lngMin
    j = lngMax
    Do
        Do While argAry(i, keyPos) < vBase
            i = i + 1
        Loop
        Do While argAry(j, keyPos) > vBase
            j = j - 1
        Loop
        If i >= j Then Exit Do
        For k = LBound(argAry, 2) To UBound(argAry, 2)
            vSwap = argAry(i, k)
            argAry(i, k) = argAry(j, k)
            argAry(j, k) = vSwap
        Next
        i = i + 1
        j = j - 1
    Loop
    If (lngMin < i - 1) Then
        Call QuickSort2(argAry, lngMin, i - 1, keyPos)
    End If
    If (lngMax > j + 1) Then
        Call QuickSort2(argAry, j + 1, lngMax, keyPos)
    End If
End Sub

'***********************************************************
' �@�\   : �t�@�C���ۑ�����(3�����z��)
' ����   :  ArrayData:�z��ϐ�
'           filePath:�t�@�C���ۑ��ꏊ
' �߂�l?� : �Ȃ�
' �쐬��  : �쓇
'***********************************************************
Sub outputOutPkg3d(ByRef ArrayData As Variant, d1Index As Long, ByRef filePath As String, Optional header)
    
    Call MakeFolder(filePath)
    
    Dim i As Long
            
    Dim fileNumber As Long
    fileNumber = FreeFile
                
    Open filePath For Output As #fileNumber
    
    If Not IsMissing(header) Then
        Print #fileNumber, header & vbCrLf;
    End If
    
    For i = LBound(ArrayData, 2) To UBound(ArrayData, 2)
        For j = LBound(ArrayData, 3) To UBound(ArrayData, 3)
            If j = UBound(ArrayData, 3) Then
                Print #fileNumber, ArrayData(d1Index, i, j);
            Else
                Print #fileNumber, ArrayData(d1Index, i, j) & ",";
            End If
        Next j
        Print #fileNumber, "," & startBlock & vbCrLf;
    Next i
    Close #fileNumber
End Sub


'***********************************************************
' �@�\   : �t�@�C���ۑ�����
' ����   :  ArrayData:�z��ϐ�
'           filePath:�t�@�C���ۑ��ꏊ
' �߂�l?� : �Ȃ�
' �쐬��  : �쓇
'***********************************************************
Sub OutputText(ByRef ArrayData As Variant, ByRef filePath As String)
    
    Call MakeFolder(filePath)
    
    Dim i As Long
            
    Dim fileNumber As Long
    fileNumber = FreeFile
        
    Open filePath For Output As #fileNumber
    For i = LBound(ArrayData, 1) To UBound(ArrayData, 1)
        For j = LBound(ArrayData, 2) To UBound(ArrayData, 2)
            If j = UBound(ArrayData, 2) Then
                Print #fileNumber, ArrayData(i, j);
            Else
                Print #fileNumber, ArrayData(i, j) & ",";
            End If
        Next j
        Print #fileNumber, vbCrLf;
    Next i
    Close #fileNumber
End Sub

'***********************************************************
' �@�\   : �t�@�C���ۑ�����
' ����   :  ArrayData:�z��ϐ�
'           filePath:�t�@�C���ۑ��ꏊ
' �߂�l?� : �Ȃ�
' �쐬��  : �쓇
'***********************************************************
Sub OutputText1D(ByRef ArrayData As Variant, ByRef filePath As String, Optional logHeader)
    
    Call MakeFolder(filePath)
    
    Dim i As Long
            
    Dim fileNumber As Long
    fileNumber = FreeFile
        
    Open filePath For Output As #fileNumber
    
    If Not IsMissing(logHeader) Then
        Print #fileNumber, logHeader;
        Print #fileNumber, vbCrLf;
    End If
    
    For i = LBound(ArrayData) To UBound(ArrayData)
        Print #fileNumber, ArrayData(i);
        Print #fileNumber, vbCrLf;
    Next i
    Close #fileNumber
End Sub


'***********************************************************
' �@�\   : �t�@�C���ۑ�����
' ����   :  ArrayData:�z��ϐ�
'           filePath:�t�@�C���ۑ��ꏊ
' �߂�l?� : �Ȃ�
' �쐬��  : �쓇
'***********************************************************
Sub AppendText1D(ByRef ArrayData As Variant, ByRef filePath As String, Optional logHeader)
    
    Call MakeFolder(filePath)
    
    Dim i As Long
            
    Dim fileNumber As Long
    fileNumber = FreeFile
        
    Open filePath For Append As #fileNumber
    
    If Not IsMissing(logHeader) Then
        If Dir(filePath) = "" Then
            Print #fileNumber, logHeader;
            Print #fileNumber, vbCrLf;
        End If
    End If
    
    For i = LBound(ArrayData) To UBound(ArrayData)
        Print #fileNumber, ArrayData(i);
        Print #fileNumber, vbCrLf;
    Next i
    Close #fileNumber
End Sub

'***********************************************************
' �@�\   : �t�@�C���ۑ�����
' ����   :  ArrayData:�z��ϐ�
'           filePath:�t�@�C���ۑ��ꏊ
' �߂�l?� : �Ȃ�
' �쐬��  : �쓇
'***********************************************************
Function AppendText(ByRef ArrayData As Variant, ByRef filePath As String)
    
    Call MakeFolder(filePath)
    
    Dim i As Long
            
    Dim fileNumber As Long
    fileNumber = FreeFile
    
    Open filePath For Append As #fileNumber
    
    On Error GoTo Err
    For i = LBound(ArrayData, 1) To UBound(ArrayData, 1)
        For j = LBound(ArrayData, 2) To UBound(ArrayData, 2)
            If j = UBound(ArrayData, 2) Then
                Print #fileNumber, ArrayData(i, j);
            Else
                Print #fileNumber, ArrayData(i, j) & ",";
            End If
        Next j
        Print #fileNumber, vbCrLf;
    Next i
    Close #fileNumber
    Exit Function
Err:
    MsgBox "���L�̃t�@�C���ۑ����e�ɃG���[���܂܂�Ă��܂�" & vbCrLf & "�s��:" & i & vbCrLf & "��:" & j & vbCrLf & "�ۑ��p�X:" & filePath, vbCritical
    End
End Function

'***********************************************************
' �@�\   : �t�@�C���ۑ�����
' ����   :  strText:�ϐ�
'           filePath:�t�@�C���ۑ��ꏊ
' �߂�l?� : �Ȃ�
' �쐬��  : �쓇
'***********************************************************
Sub OutputSingleText(strText, filePath As String)
    Call MakeFolder(filePath)
    
    Dim i As Long
            
    Dim fileNumber As Long
    fileNumber = FreeFile
    
    Open filePath For Output As #fileNumber
                
    Print #fileNumber, strText;
    Print #fileNumber, vbCrLf;
    
    Close #fileNumber
End Sub

'***********************************************************
' �@�\   : �t�@�C���ۑ�����
' ����   :  strText:�ϐ�
'           filePath:�t�@�C���ۑ��ꏊ
' �߂�l?� : �Ȃ�
' �쐬��  : �쓇
'***********************************************************
Sub AppendSingleText(strText, filePath As String, Optional logHeader)
        Call MakeFolder(filePath)
        
        Dim i As Long
                
        Dim fileNumber As Long
        fileNumber = FreeFile
        
        Open filePath For Append As #fileNumber
                    
        If Not IsMissing(logHeader) Then
            If Dir(filePath) = "" Then
                Print #fileNumber, logHeader;
                Print #fileNumber, vbCrLf;
            End If
        End If
                    
        Print #fileNumber, strText;
        Print #fileNumber, vbCrLf;
        
        Close #fileNumber
End Sub

'***********************************************************
' �@�\   : �t�H���_�̍쐬
' ����   : �t�H���_���́i��΃p�X�j
' �߂�l : �Ȃ�
' �쐬��  : �t�R
'***********************************************************

Function MakeFolder(ByVal TargetPath As String)
    Dim objFS As Object
    Set objFS = CreateObject("Scripting.FileSystemObject")
    Dim strParent As String
    
    If TargetPath = "" Then
    Stop
    End If
 
    If TargetPath Like "*.*" Then
        TargetPath = objFS.GetParentFolderName(TargetPath)
    End If
 
    strParent = objFS.GetParentFolderName(TargetPath)
    
    If Not objFS.FolderExists(strParent) Then
       Call MakeFolder(strParent)
    End If
     
    If Not objFS.FolderExists(TargetPath) Then
       objFS.CreateFolder (TargetPath)
    End If
    
    Set objFS = Nothing
End Function

'***********************************************************
' �@�\   : �Ώۃf�B���N�g�����̃T�u�f�B���N�g�������܂ރt�@�C�����X�g�擾
' ����   : dirPath�i�Ώۃf�B���N�g���̐�΃p�X�j
' �߂�l?� : �t�@�C�������X�g�i�z��j
' �쐬��  : �t�R
'***********************************************************
Function MakeFilesList(Path As String, wildcard As String)
    Dim filenames() As String
    Dim buf As String, f As Object
    buf = Dir(Path & "\" & wildcard)
    
    Dim Cnt As Long: Cnt = 0
    '�Ώۃf�B���N�g���K�w�̃t�@�C�����擾
    Do While buf <> ""
        Cnt = Cnt + 1
        ReDim Preserve filenames(Cnt)
        filenames(Cnt - 1) = Path & "\" & buf
        buf = Dir()
    Loop
    If Cnt = 0 Then
        ReDim Preserve filenames(0)
        '�f�B���N�g�������݂��Ȃ��Ƃ��p
        Dim buf2 As String
        buf2 = Dir(Path, vbDirectory)
        If buf2 = "" Then
            ReDim filenames(0)
            MakeFilesList = filenames
            Exit Function
        End If
    End If
    
    
    
    '�Ώۃf�B���N�g���̃T�u�f�B���N�g���ȉ��̊K�w�̃t�@�C�����擾
    With CreateObject("Scripting.FileSystemObject")
        For Each f In .GetFolder(Path).SubFolders
            Dim tmp_filenames() As String
            tmp_filenames = MakeFilesList(f.Path, wildcard)
            
            Dim size_of_mtx As Long
            size_of_mtx = UBound(filenames)
            If Len(filenames(0)) = 0 Then
                size_of_mtx = 0
            End If
            If tmp_filenames(0) = "" Then
                ReDim Preserve filenames(size_of_mtx)
            Else
                ReDim Preserve filenames(size_of_mtx + UBound(tmp_filenames))
                Dim i As Long
                For i = 0 To UBound(tmp_filenames)
                    filenames(size_of_mtx + i) = tmp_filenames(i)
                Next i
            End If
        Next f
    End With
    MakeFilesList = filenames
End Function


'***********************************************************
' �@�\   : CSV�Ǎ�����
' ����   :
' �߂�l : �Ȃ�
' �쐬��  : ����
'***********************************************************
Function ReadCsv(ByVal File_Target As String)
'===========================================================================
'Open�X�e�[�g�����g��Binary�ł̏����ǂݍ��݂��s���܂�
'===========================================================================
 
    Dim intFF As Long                           '�t�@�C���ԍ�
    Dim byt_buf() As Byte
    Dim var_buf
    Dim str_buf  As String                      '�����̔ėp�ϐ�
    Dim str_Strings() As String                 '�t�@�C���̒��g�S���̕�����^�z��
    Dim row As Long                             '�s���J�E���g
    Dim i As Long
     
    Dim bytSjis As String
    Dim str_Uni As String
    
    If Dir(File_Target) = "" Then Exit Function
          
    intFF = FreeFile
    Open File_Target For Binary As #intFF
        ReDim byt_buf(LOF(intFF))
        Get #intFF, , byt_buf
    Close #intFF
     
    str_Uni = StrConv(byt_buf(), vbUnicode) 'Unicode�ɕϊ�
     
    '==============================================================
    '�z�񉻗L����
    If Right(str_Uni, 1) = vbNullChar Then strUni = Left(str_Uni, Len(str_Uni) - 1)
    var_buf = Split(str_Uni, vbCrLf) '���s�R�[�h���Ƃɋ�؂��Ĕz��
    row = UBound(var_buf)            '�s���擾
    If var_buf(row) Like vbNullChar Then
        ReDim Preserve var_buf(row - 1)
    End If
    '==============================================================
     
    ReadCsv = var_buf
End Function

'***********************************************************
' �@�\   : CSV�Ǎ�����
' ����   :
' �߂�l : �Ȃ�
' �쐬��  : ����
'***********************************************************
Function ReadBigCsv(File_Target As String)
    Dim FileNum     As Long
    Dim i           As Long
    Dim n           As Long
    Dim myStr()     As String
    Dim myRec       As String
    Dim fso         As Object
    Dim TargetFile  As String
    Dim FileRow     As Long
    Dim csvArray()  As Variant
    Dim MaxCol      As Long
        
    Set fso = CreateObject("Scripting.FileSystemObject")
    FileNum = FreeFile
    
    i = 0
    MaxCol = 0
    
    ReDim Preserve csvArray(FileRow)
    Open File_Target For Input As #FileNum
    
    Do While Not EOF(FileNum)
        Line Input #FileNum, myRec
        Call AddManyItemIntoLst(csvArray, myRec)
        i = i + 1
    Loop
    Close #FileNum
    
    Call EliminateBlankRowFromLst(csvArray)
    ReadBigCsv = csvArray
End Function

'***********************************************************
' �@�\   : ���O�ۑ������i�ǋL�p�j
' ����   :  ArrayData:�z��ϐ�
'           filePath:�t�@�C���ۑ��ꏊ
' �߂�l?� : �Ȃ�
' �쐬��  : ����
'***********************************************************
Sub outLog(DateTime As Date, outContent As String, ByRef fileDir As String)
    Dim filePath As String: filePath = fileDir & "\log" & Format(nowTime, "yyyymmddhhmm") & ".txt"
    
    Dim fileNumber As Long
    fileNumber = FreeFile
    
    Open filePath For Append As #fileNumber
    '�t�@�C�������݃_�~�[�s
    If fileExist = "" Then
        Print #fileNumber, "Log No,Content"
    End If

    Print #fileNumber, Format(DateTime, "yy/mm/dd hh:mm") & "," & outContent & vbCrLf;
    Close #fileNumber
End Sub

Function CheckFileExist(filePath)
    Dim fileExist As String: fileExist = Dir(filePath)
    
    If fileExist = "" Then
        MsgBox "�w��̃t�@�C����������܂���" & vbCrLf & filePath, vbCritical
        End
    End If
End Function

'�S�V�[�g�̃t�B���^�[��OFF�ɂ���
Function showAllData(WB As Workbook)
    Dim WS As Worksheet '���[�N�V�[�g�̃I�u�W�F�N�g�ϐ��Ƃ���WS���`'
    For Each WS In WB.Worksheets   '�u�b�N���̃��[�N�V�[�g�̏W���iWorksheets)���烏�[�N�V�[�g��1����WS�Ɋi�['
        If WS.FilterMode = True Then
            WS.showAllData
        End If
    Next WS
End Function

'***********************************************************
' �@�\   : �V�[�g���t�@�C���֏�������
' �߂�l?� : �Ȃ�
' �쐬��  : ����
'***********************************************************

Sub SaveSheet(stName, savePath)
    With ThisWorkbook.Worksheets(stName)
    
    lastRow = .Range("A1").SpecialCells(xlLastCell).row
    lastCol = .Range("A1").SpecialCells(xlLastCell).Column
        
    saveRange = .Range(.Cells(1, 1), .Cells(lastRow, lastCol))
    
    If Dir(savePath) <> "" Then
        msgResult = MsgBox("�t�@�C�������݂��܂����㏑���܂���", Buttons:=vbYesNo)
        
        If msgResult = vbYes Then
            Call OutputText(saveRange, CStr(savePath))
        Else
            End
        End If
    Else
        Call OutputText(saveRange, CStr(savePath))
    End If
    
    End With
    
    MsgBox "�ۑ����܂���", vbInformation
End Sub


'***********************************************************
' �@�\   : �t�@�C�����V�[�g�ɓǂݍ���
' ����   :
' �߂�l?� : �Ȃ�
' �쐬��  : ����
'***********************************************************

Sub ReadSheet(stName, savePath)
    With ThisWorkbook.Worksheets(stName)
    
    csvLst = ReadCsv(savePath)
    csvLst = ConvertDimensionToSplitComma(csvLst)
        
    .Cells.ClearContents
    .Range(.Cells(1, 1), .Cells(UBound(csvLst, 1), UBound(csvLst, 2))) = csvLst
    End With
    
    MsgBox "�Ǎ��݂܂���", vbInformation
End Sub

'***********************************************************
' �@�\   : �u�b�N���J���Ă��邩�ǂ�������
' ����   : �Ȃ�
' �߂�l : �Ȃ�
'***********************************************************
Function IsBookOpened(a_sFilePath) As Boolean
    On Error Resume Next
    
    '// �ۑ��ς݂̃u�b�N������
    Open a_sFilePath For Append As #1
    Close #1
    
    If Err.Number > 0 Then
        '// ���ɊJ����Ă���ꍇ
        IsBookOpened = True
    Else
        '// �J����Ă��Ȃ��ꍇ
        IsBookOpened = False
    End If
End Function

'***********************************************************
' �@�\   : ���L�u�b�N���J���Ă��邩�ǂ�������
' ����   : �Ȃ�
' �߂�l : �Ȃ�
'***********************************************************
Function IsShareBookOpened(a_sFilePath, Optional returnBook As Workbook) As Boolean
    Dim myChkBook As Workbook

    On Error GoTo ErrHdl
    fileName = Dir(a_sFilePath)
    If IsMissing(returnBook) Then
        Set myChkBook = Workbooks(fileName)
    Else
        Set returnBook = Workbooks(fileName)
    End If

    IsShareBookOpened = True
    Exit Function
    
ErrHdl:
    IsShareBookOpened = False

End Function

'***********************************************************
' �@�\   : ���L�u�b�N���J���Ă��邩�ǂ�������
' ����   : �Ȃ�
' �߂�l : �Ȃ�
'***********************************************************
Function CheckFileOpened(filePath)
    If Dir(filePath) <> "" Then
        If IsBookOpened(filePath) Then
            MsgBox "�o�̓t�@�C�����J����Ă��邽�ߕ��Ă�������" & vbCrLf & filePath, vbCritical
            End
        End If
    End If
End Function

'***********************************************************
' �@�\   : 1�������ɔz��ɕ�������
' ����   : �Ȃ�
' �߂�l : �Ȃ�
'***********************************************************
Function SplitEachCharacter(TXT)
  Dim arr() As Variant
  Dim i As Long
  ReDim arr(Len(TXT) - 1)
  For i = 0 To UBound(arr)
    arr(i) = Mid(TXT, i + 1, 1)
  Next i
  
  SplitEachCharacter = arr
End Function

'***********************************************************
' �@�\   : 1�����z���2�����z��ɕϊ�
' ����   : �Ȃ�
' �߂�l : �Ȃ�
'***********************************************************
Function ConvertDimension(arrayLst)
  Dim newLst As Variant
  maxRow = UBound(arrayLst)
  ReDim newLst(maxRow, 0)
  
  For i = LBound(arrayLst) To UBound(arrayLst)
    newLst(i, 0) = arrayLst(i)
  Next i
  
  ConvertDimension = newLst
End Function

'***********************************************************
' �@�\   : �J���}�ŋ�؂�ꂽ1�����z���2�����z��ɕϊ�
' ����   : �Ȃ�
' �߂�l : �Ȃ�
'***********************************************************
Function ConvertDimensionToSplitComma(arrayLst) As Variant
  Dim newLst As Variant
  minRow = LBound(arrayLst)
  maxRow = UBound(arrayLst)
  If minRow = 0 Then
    minRow = minRow + 1
    maxRow = maxRow + 1
    ReDim Preserve arrayLst(1 To maxRow)
  End If
  MaxCol = 1
  For i = minRow To maxRow
    tmp = Split(arrayLst(i), ",")
    If MaxCol <= UBound(tmp) Then
        MaxCol = UBound(tmp) + 1
    End If
  Next
  ReDim newLst(1 To maxRow, 1 To MaxCol)
  
  For i = LBound(arrayLst) To UBound(arrayLst)
    arrayRowLst = Split(arrayLst(i), ",")
    For j = LBound(arrayRowLst) To UBound(arrayRowLst)
        newLst(i, j + 1) = arrayRowLst(j)
    Next j
  Next i
  
  ConvertDimensionToSplitComma = newLst
End Function

'***********************************************************
' �@�\   : �J���}�ŋ�؂�ꂽ1�����z���2�����z��ɕϊ��@���z��C���f�b�N�X�̊J�n��0
' ����   : �Ȃ�
' �߂�l : �Ȃ�
'***********************************************************
Function ConvertDimension1Dto2D(arrayLst) As Variant
  Dim newLst As Variant
  minRow = LBound(arrayLst)
  maxRow = UBound(arrayLst)
  MaxCol = 0
  For i = minRow To maxRow
    tmp = Split(arrayLst(i), ",")
    If MaxCol <= UBound(tmp) Then
        MaxCol = UBound(tmp)
    End If
  Next
  ReDim newLst(maxRow, MaxCol)
  
  For i = LBound(arrayLst) To UBound(arrayLst)
    arrayRowLst = Split(arrayLst(i), ",")
    For j = LBound(arrayRowLst) To UBound(arrayRowLst)
        newLst(i, j) = arrayRowLst(j)
    Next j
  Next i
  
  ConvertDimension1Dto2D = newLst
End Function


'***********************************************************
' �@�\   : 2�����z���1�����z��ɕϊ�
' ����   : �Ȃ�
' �߂�l : �Ȃ�
'***********************************************************
Function ConvertDimension2Dto1D(arrayLst)
    Dim newLst As Variant
    minRow = LBound(arrayLst)
    maxRow = UBound(arrayLst)
    minCol = LBound(arrayLst, 2)
    MaxCol = UBound(arrayLst, 2)
    ReDim newLst(minRow To maxRow)
  
    For i = minRow To maxRow
        For j = minCol To MaxCol
            If j = minCol Then
                joinRow = arrayLst(i, j)
            Else
                joinRow = joinRow & "," & arrayLst(i, j)
            End If
        Next j
        newLst(i) = joinRow
    Next i
  
    ConvertDimension2Dto1D = newLst
End Function

'***********************************************************
' �@�\   : �t�@�C���ۑ�����
' ����   :  ArrayData:�z��ϐ�
'           filePath:�t�@�C���ۑ��ꏊ
' �߂�l?� : �Ȃ�
' �쐬��  : ����
'***********************************************************
Sub AppendString(outText, headerText, filePath)
    Dim fso
    Set fso = CreateObject("Scripting.FileSystemObject")
        
    Dim outputFile
    
    If Dir(filePath) = "" Then
        Call MakeFolder(CStr(filePath))
        Set outputFile = fso.OpenTextFile(filePath, 2, True)
        outputFile.Write (headerText)
        outputFile.Write (vbCrLf)
        outputFile.Close
    End If
    Set outputFile = fso.OpenTextFile(filePath, 8, False)
        
    outputFile.Write (outText)
    outputFile.Write (vbCrLf)
    
    ' �o�b�t�@�� Flush ���ăt�@�C�������
    outputFile.Close
    Set fso = Nothing
End Sub


'***********************************************************
' �@�\   : �������x�v��
' ����   :  �������x�ۑ��ϐ�
'           �O��ō�����
' �߂�l?� : �Ȃ�
' �쐬��  : ����
'***********************************************************
Function CalcProcessSpeed(ByRef saveTime As Double)
    nowProcessTime = Timer
    
    '�������x��ۑ�
    If mileStoneTime <> 0 Then
        saveTime = saveTime + nowProcessTime - mileStoneTime
    End If
    
    '�}�C���X�g�[���̎������X�V
    mileStoneTime = nowProcessTime
End Function

'***********************************************************
' �@�\   : �g�ݍ��킹�̎擾
' ����   : ���̔z��
'          �g�ݍ��킹��
' �߂�l� : �g�ݍ��킹���ʂ̓񎟌��z��
' �쐬��  : ����
'***********************************************************
Function GetCombination(aryIn, pCnt)
    Dim aryOut
    Dim aryNum1
    Dim aryNum2
    Dim aryTemp
    Dim i1 As Long
    Dim i2 As Long
    Dim ix As Long
    Dim sTemp1 As String
    Dim sTemp2 As String
    Dim flg As Boolean
  
    '���͔z�񂩂�w�萔�����o��
    '�܂��́A1,2,3,4,5���쐬
    ReDim aryTemp(UBound(aryIn))
    For i1 = 0 To UBound(aryIn)
        aryTemp(i1) = i1
    Next
    '1,2,3,4,5�̏���쐬
    Call permutation(aryTemp, aryNum1)
    '1,2,3,4,5�̏��񂩂�擪�̎w�萔�����o��
    '�����͑g�ݍ��킹����肽���̂ŏ����Ⴂ���Ȃ�
    ix = 0
    ReDim aryNum2(pCnt - 1, ix)
    For i2 = 0 To UBound(aryNum1, 2)
        sTemp1 = ""
        sTemp2 = ""
        flg = True
        If i2 = 0 Then
            sTemp1 = "1"
            sTemp2 = "2"
        Else
            For i1 = 0 To pCnt - 1
                sTemp1 = sTemp1 & "_" & aryNum1(i1, i2 - 1)
                sTemp2 = sTemp2 & "_" & aryNum1(i1, i2)
                If i1 > 0 Then
                    If aryNum1(i1 - 1, i2) > aryNum1(i1, i2) Then
                        flg = False
                    End If
                End If
            Next
        End If
        If sTemp1 <> sTemp2 And flg = True Then
            ReDim Preserve aryNum2(pCnt - 1, ix)
            For i1 = 0 To pCnt - 1
                aryNum2(i1, ix) = aryNum1(i1, i2)
            Next
            ix = ix + 1
        End If
    Next
  
    '���͔z��̑g�ݍ��킹�ɖ߂�
    aryOut = aryNum2
    For i2 = 0 To UBound(aryNum2, 2)
        For i1 = 0 To pCnt - 1
            aryOut(i1, i2) = aryIn(aryNum2(i1, i2))
        Next
    Next
    GetCombination = aryOut
End Function

Public Sub permutation(ByRef aryIn, ByRef aryOut, Optional ByVal i As Long = 0)
    Dim j As Long
    Dim ix As Long
    Dim sTemp
    Dim ary
    If i < UBound(aryIn) Then
        For j = i To UBound(aryIn)
            '�z������ւ���
            ary = aryIn
            sTemp = aryIn(i)
            aryIn(i) = aryIn(j)
            aryIn(j) = sTemp
            '�ċA�����A�J�n�ʒu��+1
            Call permutation(aryIn, aryOut, i + 1)
            aryIn = ary '�z������ɖ߂�
        Next
    Else
        '�z��̍Ō�܂ōs�����̂ŏo��
        If IsEmpty(aryOut) Or Not IsArray(aryOut) Then
            ix = 0
            ReDim aryOut(UBound(aryIn), ix)
        Else
            ix = UBound(aryOut, 2) + 1
            ReDim Preserve aryOut(UBound(aryIn), ix)
        End If
        For j = LBound(aryIn) To UBound(aryIn)
            aryOut(j, ix) = aryIn(j)
        Next j
    End If
End Sub

Public Function getArrayDimension( _
                  ByRef TargetArray As Variant) As Long    '�c�c(1)'
  If Not IsArray(TargetArray) _
    Then getArrayDimension = False: Exit Function    '�c�c(2)'
  Dim n As Long    '�c�c(3)'
  n = 0
  Dim tmp As Long
  On Error Resume Next    '�c�c(4)'
  Do While Err.Number = 0
    n = n + 1
    tmp = UBound(TargetArray, n)
  Loop
  Err.Clear
  getArrayDimension = n - 1    '�c�c(5)'
End Function

'***********************************************************
' �@�\   : �R�}���h�v�����v�g���s����
' ����   :  �R�}���h
' �߂�l : �Ȃ�
' �쐬��  : ����
'***********************************************************
Function CommandExec(sCmd)
    Dim WSH, wExec, Result As String
    Set WSH = CreateObject("WScript.Shell")
    Set wExec = WSH.Exec("cmd /c " & sCmd)
    Do While wExec.Status = 0
        DoEvents
    Loop
    CommandExec = wExec.StdOut.ReadAll
    Set wExec = Nothing
    Set WSH = Nothing
End Function

'***********************************************************
' �@�\   : �R�~�b�g�ԍ��̎擾
' ����   : �t�@�C���p�X
' �߂�l : �R�~�b�g�ԍ�
' �쐬��  : ����
'***********************************************************
Function GetCommitNum(filePath) As String
    Dim commandStr As String
    Dim fso As Object
    Set fso = CreateObject("Scripting.FileSystemObject")
    fileName = fso.GetFileName(filePath)
    folderPath = fso.GetParentFolderName(filePath)
      
    command1 = "cd " & folderPath
    command2 = "svnversion " & fileName
    commandStr = command1 & " & " & command2
    
    commitNum = Replace(Trim(CommandExec(commandStr)), vbCrLf, "")
    If Right(commitNum, 1) = "M" Then
        commitNum = Left(commitNum, Len(commitNum) - 1)
    Else
        MsgBox "�R�~�b�g�ԍ��̎擾�Ɏ��s���܂���" & vbCrLf & commitNum
        End
    End If
    GetCommitNum = commitNum
End Function

'***********************************************************
' �@�\   : �R�~�b�g����
' ����   : �t�@�C���p�X
' �߂�l : �R�~�b�g�ԍ�
' �쐬��  : ����
'***********************************************************
Function CommitFile(filePath, logMessage) As String
    Dim commandStr As String
    Dim fso As Object
    Set fso = CreateObject("Scripting.FileSystemObject")
    fileName = fso.GetFileName(filePath)
    folderPath = fso.GetParentFolderName(filePath)
      
    command1 = "cd " & folderPath
    command2 = "svn commit -m " & logMessage & " " & fileName
    commandStr = command1 & " & " & command2

    CommitFile = CommandExec(commandStr)
End Function

'***********************************************************
' �@�\   : 1�����z��̏d���폜
' ����   : �z��
' �߂�l : �d�����폜�����z��
' �쐬��  : ����
'***********************************************************
Function RemoveDuplicate(arrayLst)
    Dim isDuplicate As Boolean
    Dim checkDuplicateDic As Variant
    Set checkDuplicateDic = CreateObject("Scripting.Dictionary")
    
    For i = LBound(arrayLst) To UBound(arrayLst)
        rowValue = arrayLst(i)
        If Not checkDuplicateDic.exists(rowValue) Then
            checkDuplicateDic.Add rowValue, 1
        Else
            isDuplicate = True
        End If
    Next i
    
    If isDuplicate Then
        Dim newArrayLst As Variant
        maxIndex = checkDuplicateDic.Count - 1
        ReDim newArrayLst(maxIndex)
        Count = 0
        For Each rowValue In checkDuplicateDic
            newArrayLst(Count) = rowValue
            Count = Count + 1
        Next
        RemoveDuplicate = newArrayLst
    Else
        RemoveDuplicate = arrayLst
    End If
End Function

'***********************************************************
' �@�\   : 2�����z�񂩂�w�肵������擾
' ����   : 2�����z��A�w���
' �߂�l : 1��݂̂�2�����z��
' �쐬��  : ����
'***********************************************************
Function ExtractColumn(arrayLst, targetIndex) As Variant
    Dim returnLst As Variant
    maxRow = UBound(arrayLst)
    ReDim returnLst(1 To maxRow, 1 To 1)
    For i = LBound(arrayLst) To UBound(arrayLst)
        returnLst(i, 1) = arrayLst(i, targetIndex)
    Next i
    ExtractColumn = returnLst
End Function

'***********************************************************
' �@�\   : 2�����z��̍s��ϊ�����
' ����   : 2�����z��
' �߂�l : �s��ϊ�����2�����z��
' �쐬��  : ����
'***********************************************************
Function Transpose2DLst(arrayLst) As Variant
    maxRow = UBound(arrayLst, 2)
    MaxCol = UBound(arrayLst)
    minRow = LBound(arrayLst, 2)
    minCol = LBound(arrayLst)
    
    Dim newArrayLst As Variant
    ReDim newArrayLst(minRow To maxRow, minCol To MaxCol)
    
    For i = minRow To maxRow
        For j = minCol To MaxCol
            newArrayLst(i, j) = arrayLst(j, i)
        Next j
    Next i
    Transpose2DLst = newArrayLst
End Function

'***********************************************************
' �@�\   : 1�����z��̍s�ǉ�����
' ����   : 1�����z��A�ǉ��e�L�X�g
' �߂�l : �s�ǉ�����1�����z��
' �쐬��  : ����
'***********************************************************
Function AddRow(arrayLst, addRowText) As Variant
    exMaxIndex = UBound(arrayLst)
    maxIndex = UBound(arrayLst) + UBound(addRowText)
    ReDim arrayLst(maxIndex)
    For i = LBound(addRowText) To UBound(addRowText)
        arrayLst(exMaxIndex + i) = addRowText(i)
    Next i
    AddRow = arrayLst
End Function

'***********************************************************
' �@�\   : �����������w�萔���ׂ�����������
' ����   : �����A�J��Ԃ���
' �߂�l : ��������������
' �쐬��  : ����
'***********************************************************
Function CombineSameCharacter(character As String, cycleNum As Long) As String
    Dim arrayLst As Variant
    ReDim arrayLst(1 To cycleNum)
    
    For i = LBound(arrayLst) To UBound(arrayLst)
        arrayLst(i) = character
    Next i
    
    CombineSameCharacter = Join(arrayLst, "")
End Function

'***********************************************************
' �@�\   : 2�����z���2����Collection�ɕϊ�����
' ����   : 2�����z��
' �߂�l : 2����Collection
' �쐬��  : ����
'***********************************************************
Function ConvertListToCollection2D(arrayLst As Variant) As Variant
    Dim newCollection As Object
    Set newCollection = New Collection
    For i = LBound(arrayLst) To UBound(arrayLst)
        Dim rowCollection As Object
        Set rowCollection = New Collection
        For j = LBound(arrayLst, 2) To UBound(arrayLst, 2)
            rowCollection.Add arrayLst(i, j)
        Next j
        newCollection.Add rowCollection
    Next i
    
    Set ConvertListToCollection2D = newCollection
End Function

'***********************************************************
' �@�\   : 2����Collection��2�����z��ɕϊ�����
' ����   : 2����Collection
' �߂�l : 2�����z��
' �쐬��  : ����
'***********************************************************
Function ConvertCollectionToList2D(myCol As Variant)
    Dim newArray As Variant
    maxRow = myCol.Count
    ReDim newArray(1 To maxRow, 1 To 1)
    
    For i = 1 To myCol.Count
        Set rowCol = myCol(i)
        maxColumn = rowCol.Count
        ReDim Preserve newArray(1 To maxRow, 1 To maxColumn)
        For j = 1 To rowCol.Count
            newArray(i, j) = rowCol(j)
        Next
    Next
    
    ConvertCollectionToList2D = newArray
End Function

'***********************************************************
' �@�\   : 2�����z��̓���s��2����Collection�̓���s��������
' ����   : 2����Collection�A2�����z��A����s
' �߂�l : 2�����z��
' �쐬��  : ����
'***********************************************************
Function ReplaceRowOfCollectionToList(myCol As Variant, myLst As Variant, replaceRow As Long)
    Set rowCol = myCol(replaceRow)
    If UBound(myLst, 2) < rowCol.Count Then
        maxLoop = UBound(myLst, 2)
    Else
        maxLoop = rowCol.Count
    End If
    
    For i = 1 To maxLoop
        myLst(replaceRow, i) = rowCol(i)
    Next
    
    ReplaceRowOfCollectionToList = myLst
End Function

'***********************************************************
' �@�\   : OFF�̍s���Ȃ�
' ����   : 2�����z��
' �߂�l :
' �쐬��  : ����
'***********************************************************
Function RemoveOffRow(arrayLst, offCol)
    Set collection2d = ConvertListToCollection2D(arrayLst)
    
    For i = 1 To collection2d.Count - 1
        Set collection1D = collection2d(i)
        If collection1D(offCol) <> "1" Then
            If removeIndex = "" Then
                removeIndex = i
            Else
                removeIndex = removeIndex & "|" & i
            End If
        End If
    Next i
    
    removeIndexLst = Split(removeIndex, "|")
    
    For i = UBound(removeIndexLst) To LBound(removeIndexLst) Step -1
        removeIndex = CLng(removeIndexLst(i))
        collection2d.Remove removeIndex
    Next i
    
    arrayLst = ConvertCollectionToList2D(collection2d)
End Function

'***********************************************************
' �@�\   : �z��̓Ǎ�
' ����   : �V�[�g���A�z��̎擾�J�n�s�A�z��̎擾�񐔂����߂�J�����s
' �߂�l : ��荞��2�����z��
' �쐬��  : ����
'***********************************************************
Function TakeArrayFromSheet(sheetName As String, readRowWithoutHeader As Long, columnSizeRow As Long)

    With ThisWorkbook.Worksheets(sheetName)
        startRow = readRowWithoutHeader
        lastRow = .Cells(Rows.Count, 1).End(xlUp).row
        lastCol = .Cells(columnSizeRow, 1).End(xlToRight).Column
                
        TakeArrayFromSheet = .Range(.Cells(startRow, 1), .Cells(lastRow, lastCol))
    End With

End Function

Public Function GetGUID() As String
 '(c) 2000 Gus Molina
 Dim udtGUID As GUID
 If (CoCreateGuid(udtGUID) = 0) Then
  GetGUID = _
   String(8 - Len(Hex$(udtGUID.Data1)), "0") & Hex$(udtGUID.Data1) & "-" & _
   String(4 - Len(Hex$(udtGUID.Data2)), "0") & Hex$(udtGUID.Data2) & "-" & _
   String(4 - Len(Hex$(udtGUID.Data3)), "0") & Hex$(udtGUID.Data3) & "-" & _
   IIf((udtGUID.Data4(0) < &H10), "0", "") & Hex$(udtGUID.Data4(0)) & _
   IIf((udtGUID.Data4(1) < &H10), "0", "") & Hex$(udtGUID.Data4(1)) & "-" & _
   IIf((udtGUID.Data4(2) < &H10), "0", "") & Hex$(udtGUID.Data4(2)) & _
   IIf((udtGUID.Data4(3) < &H10), "0", "") & Hex$(udtGUID.Data4(3)) & _
   IIf((udtGUID.Data4(4) < &H10), "0", "") & Hex$(udtGUID.Data4(4)) & _
   IIf((udtGUID.Data4(5) < &H10), "0", "") & Hex$(udtGUID.Data4(5)) & _
   IIf((udtGUID.Data4(6) < &H10), "0", "") & Hex$(udtGUID.Data4(6)) & _
   IIf((udtGUID.Data4(7) < &H10), "0", "") & Hex$(udtGUID.Data4(7))
 End If
End Function

'�}�[�W�\�[�g����
Public Function MergeSort2Asc(ByRef arr As Variant, ByVal col As Long)
    Dim irekae As Variant
    Dim indexer As Variant
    Dim tmp1() As Variant
    Dim tmp2() As Variant
    Dim i As Long
    ReDim irekae(LBound(arr, 1) To UBound(arr, 1))
    ReDim indexer(LBound(arr, 1) To UBound(arr, 1))
    ReDim tmp1(LBound(arr, 1) To UBound(arr, 1))
    ReDim tmp2(LBound(arr, 1) To UBound(arr, 1))
    For i = LBound(arr, 1) To UBound(arr, 1) Step 2
        If i + 1 > UBound(arr, 1) Then
            irekae(i) = arr(i, col)
            indexer(i) = i
            Exit For
        End If
        If arr(i + 1, col) < arr(i, col) Then
            irekae(i) = arr(i + 1, col)
            irekae(i + 1) = arr(i, col)
            indexer(i) = i + 1
            indexer(i + 1) = i
        Else
            irekae(i) = arr(i, col)
            irekae(i + 1) = arr(i + 1, col)
            indexer(i) = i
            indexer(i + 1) = i + 1
        End If
    Next
    Dim st1 As Long
    Dim en1 As Long
    Dim st2 As Long
    Dim en2 As Long
    Dim n As Long
    i = 1
    Do While i * 2 <= UBound(arr, 1)
        i = i * 2
        n = 0
        Do While en2 + i - 1 < UBound(arr, 1)
            n = n + 1
            st1 = i * 2 * (n - 1) + LBound(arr, 1)
            en1 = i * 2 * (n - 1) + i - 1 + LBound(arr, 1)
            st2 = en1 + 1
            en2 = IIf(st2 + i - 1 >= UBound(arr, 1), UBound(arr, 1), st2 + i - 1)
            Call merge2(irekae, indexer, tmp1, tmp2, st1, en1, st2, en2)
        Loop
        en2 = 0
    Loop
    Dim ret As Variant
    ReDim ret(LBound(arr, 1) To UBound(arr, 1), LBound(arr, 2) To UBound(arr, 2))
    For i = LBound(arr, 1) To UBound(arr, 1)
        For n = LBound(arr, 2) To UBound(arr, 2)
            If IsObject(arr(indexer(i), n)) Then
                Set ret(i, n) = arr(indexer(i), n)
            Else
                ret(i, n) = arr(indexer(i), n)
            End If
        Next
    Next
    arr = ret
End Function

Private Sub merge2(ByRef irekae As Variant, _
ByRef indexer As Variant, _
ByRef tmpArr() As Variant, _
ByRef tmpIndexer() As Variant, _
ByVal st1 As Long, _
ByVal en1 As Long, _
ByVal st2 As Long, _
ByVal en2 As Long)
    Dim j As Long
    Dim n As Long
    Dim i As Long
    For i = st1 To en2
        tmpArr(i) = irekae(i)
        tmpIndexer(i) = indexer(i)
    Next
    j = st1
    n = st2
    Do While (j < en1 + 1 Or n < en2 + 1)
        If n >= en2 + 1 Then
            irekae(j + n - st2) = tmpArr(j)
            indexer(j + n - st2) = tmpIndexer(j)
            j = j + 1
        ElseIf j < en1 + 1 And tmpArr(j) <= tmpArr(n) Then
            irekae(j + n - st2) = tmpArr(j)
            indexer(j + n - st2) = tmpIndexer(j)
            j = j + 1
        Else
            irekae(j + n - st2) = tmpArr(n)
            indexer(j + n - st2) = tmpIndexer(n)
            n = n + 1
        End If
    Loop
End Sub

'�}�[�W�\�[�g�~��
Public Function MergeSort2Desc(ByRef arr As Variant, ByVal col As Long)
    Dim irekae As Variant
    Dim indexer As Variant
    Dim tmp1() As Variant
    Dim tmp2() As Variant
    Dim i As Long
    ReDim irekae(LBound(arr, 1) To UBound(arr, 1))
    ReDim indexer(LBound(arr, 1) To UBound(arr, 1))
    ReDim tmp1(LBound(arr, 1) To UBound(arr, 1))
    ReDim tmp2(LBound(arr, 1) To UBound(arr, 1))
    For i = LBound(arr, 1) To UBound(arr, 1) Step 2
        If i + 1 > UBound(arr, 1) Then
            irekae(i) = arr(i, col)
            indexer(i) = i
            Exit For
        End If
        If arr(i + 1, col) > arr(i, col) Then
            irekae(i) = arr(i + 1, col)
            irekae(i + 1) = arr(i, col)
            indexer(i) = i + 1
            indexer(i + 1) = i
        Else
            irekae(i) = arr(i, col)
            irekae(i + 1) = arr(i + 1, col)
            indexer(i) = i
            indexer(i + 1) = i + 1
        End If
    Next
    Dim st1 As Long
    Dim en1 As Long
    Dim st2 As Long
    Dim en2 As Long
    Dim n As Long
    i = 1
    Do While i * 2 <= UBound(arr, 1)
        i = i * 2
        n = 0
        Do While en2 + i - 1 < UBound(arr, 1)
            n = n + 1
            st1 = i * 2 * (n - 1) + LBound(arr, 1)
            en1 = i * 2 * (n - 1) + i - 1 + LBound(arr, 1)
            st2 = en1 + 1
            en2 = IIf(st2 + i - 1 >= UBound(arr, 1), UBound(arr, 1), st2 + i - 1)
            Call merge2desc(irekae, indexer, tmp1, tmp2, st1, en1, st2, en2)
        Loop
        en2 = 0
    Loop
    Dim ret As Variant
    ReDim ret(LBound(arr, 1) To UBound(arr, 1), LBound(arr, 2) To UBound(arr, 2))
    For i = LBound(arr, 1) To UBound(arr, 1)
        For n = LBound(arr, 2) To UBound(arr, 2)
            If IsObject(arr(indexer(i), n)) Then
                Set ret(i, n) = arr(indexer(i), n)
            Else
                ret(i, n) = arr(indexer(i), n)
            End If
        Next
    Next
    arr = ret
End Function

Private Sub merge2desc(ByRef irekae As Variant, _
ByRef indexer As Variant, _
ByRef tmpArr() As Variant, _
ByRef tmpIndexer() As Variant, _
ByVal st1 As Long, _
ByVal en1 As Long, _
ByVal st2 As Long, _
ByVal en2 As Long)
    Dim j As Long
    Dim n As Long
    Dim i As Long
    For i = st1 To en2
        tmpArr(i) = irekae(i)
        tmpIndexer(i) = indexer(i)
    Next
    j = st1
    n = st2
    Do While (j < en1 + 1 Or n < en2 + 1)
        If n >= en2 + 1 Then
            irekae(j + n - st2) = tmpArr(j)
            indexer(j + n - st2) = tmpIndexer(j)
            j = j + 1
        ElseIf j < en1 + 1 And tmpArr(j) >= tmpArr(n) Then
            irekae(j + n - st2) = tmpArr(j)
            indexer(j + n - st2) = tmpIndexer(j)
            j = j + 1
        Else
            irekae(j + n - st2) = tmpArr(n)
            indexer(j + n - st2) = tmpIndexer(n)
            n = n + 1
        End If
    Loop
End Sub

Function Array2DToStringArray2D(arrayLst, stWork)
    With ThisWorkbook.Worksheets(stWork)
    
    .Cells.Clear
    .Range("A:G").NumberFormatLocal = "@"
    .Range(.Cells(1, 1), .Cells(UBound(arrayLst, 1), UBound(arrayLst, 2))) = arrayLst
    arrayLst = .Range(.Cells(1, 1), .Cells(UBound(arrayLst, 1), UBound(arrayLst, 2)))
    
    End With
    
    Array2DToStringArray2D = arrayLst
End Function

'�w�W���������ϊ���������
Function AddSmallChar(indexName)
    If Left(indexName, 2) = "ZZ" Then
        AddSmallChar = "0" & indexName
        Exit Function
    End If

    Dim reg
    Set reg = CreateObject("VBScript.RegExp")
     
    '���K�\���̎w��
    With reg
        .pattern = "^[A-Z][A-Z][0-9]{3}"       '�p�^�[�����w��
        .IgnoreCase = False '�啶���Ə���������ʂ��邩(False)�A���Ȃ���(True)
    End With
    
    If reg.test(indexName) Then
        AddSmallChar = indexName
        Exit Function
    End If
    
    With reg
        .pattern = "^[a-z][A-Z][0-9]{3}"       '�p�^�[�����w��
        .IgnoreCase = False '�啶���Ə���������ʂ��邩(False)�A���Ȃ���(True)
    End With
    
    If reg.test(indexName) Then
        AddSmallChar = "s" & indexName
        Exit Function
    End If
    
    With reg
        .pattern = "^[A-Z][a-z][0-9]{3}"       '�p�^�[�����w��
        .IgnoreCase = False '�啶���Ə���������ʂ��邩(False)�A���Ȃ���(True)
    End With
    
    If reg.test(indexName) Then
        AddSmallChar = Left(indexName, 1) & "s" & Right(indexName, 4)
        Exit Function
    End If
    
    With reg
        .pattern = "^[a-z][a-z][0-9]{3}"       '�p�^�[�����w��
        .IgnoreCase = False '�啶���Ə���������ʂ��邩(False)�A���Ȃ���(True)
    End With
    
    If reg.test(indexName) Then
        AddSmallChar = "s" & Left(indexName, 1) & "s" & Right(indexName, 4)
        Exit Function
    End If
    
    MsgBox "Error"
End Function

'3�̒��ōő�̐��l�z��ԍ���Ԃ�
Function GetMaxValueInLst(arrayLst As Variant)
    sortLst = arrayLst
    Call QuickSort(sortLst)
    maxVal = sortLst(UBound(sortLst))
    
    For i = LBound(arrayLst) To UBound(arrayLst)
        If arrayLst(i) = maxVal Then
            GetMaxValueInLst = i
            Exit For
        End If
    Next
End Function

'�z����g�����ăf�[�^������
Function AddItemIntoLst(arrayLst As Variant, addItem) As Variant
'    If IsArray(arrayLst) Then
'        arrayStr = Split(arrayLst, vbCrLf)
'        newArrayStr = Join(Array(arrayStr, addItem), vbCrLf)
'        arrayLst = Split(newArrayStr, vbCrLf)
'    Else
'        ReDim arrayLst(0)
'        arrayLst(0) = addItem
'    End If

    If IsArray(arrayLst) Then
        maxIndex = UBound(arrayLst) + 1
        ReDim Preserve arrayLst(maxIndex)
        arrayLst(maxIndex) = addItem
    Else
        ReDim arrayLst(0)
        arrayLst(0) = addItem
    End If
    
    AddItemIntoLst = arrayLst
End Function

'�z����R���N�V�����ɕϊ�
Function ConvertListToCollection(a As Variant) As Collection
    Dim c As New Collection
    For Each Item In a
      c.Add Item, Item
    Next Item
    Set ConvertListToCollection = c
End Function

'�R���N�V������z��ɕϊ�
Function ConvertCollectionToList(c As Variant) As Variant
    Dim a As Variant
    maxIndex = c.Count
    ReDim a(maxIndex)
    targetIndex = 0
    For Each Item In c
        a(targetIndex) = Item
        targetIndex = targetIndex + 1
    Next Item
    ConvertCollectionToList = a
End Function

'***********************************************************
' �@�\   : 2�����z��̏d���`�F�b�N
' ����   : �z��
' �߂�l : True/False
' �쐬��  : ����
'***********************************************************
Function CheckDuplicate(arrayLst, checkCol, duplicateIndex) As Boolean
    Dim checkDuplicateDic As Variant
    Set checkDuplicateDic = CreateObject("Scripting.Dictionary")
    
    For i = LBound(arrayLst) To UBound(arrayLst)
        rowValue = arrayLst(i, checkCol)
        If Not checkDuplicateDic.exists(rowValue) Then
            checkDuplicateDic.Add rowValue, 1
        Else
            isDuplicate = True
            duplicateIndex = i
        End If
    Next i
    
    CheckDuplicate = isDuplicate
End Function


'***********************************************************
' �@�\   : �z�񂩂�w�b�_�[�𗎂Ƃ�
' ����   : �z��
' �߂�l : �z��
' �쐬��  : ����
'***********************************************************
Function RemoveHeaderFromLst(arrayLst As Variant, headerCount)
    If UBound(arrayLst) < headerCount Then
        MsgBox "�z�񐔂��폜����w�b�_�[�s�̕����傫���ł�"
        Stop
    End If
    
    arrayStr = Join(arrayLst, vbCrLf)
    removeCount = 0
    Do While removeCount < headerCount
        findPos = InStr(arrayStr, vbCrLf) + 1
        arrayStr = Right(arrayStr, Len(arrayStr) - findPos)
        removeCount = removeCount + 1
    Loop
    
    arrayLst = Split(arrayStr, vbCrLf)
End Function

'***********************************************************
' �@�\   : 1�����z��̗v�f���폜
' ����   : �z��
' �߂�l : �z��
' �쐬��  : ����
'***********************************************************
Public Function RemoveItemFromArray(ByRef TargetArray As Variant, ByVal deleteIndex)
'    uniqueStr = "@#$"
'    TargetArray(deleteIndex) = uniqueStr
'    arrayStr = Join(TargetArray, ",")
'    arrayStr = Replace(arrayStr, "," & uniqueStr, "")
'
'    TargetArray = Split(arrayStr, ",")

    '�폜�������v�f�ȍ~�̗v�f��O�ɂ߂ď㏑���R�s�[
    For i = deleteIndex To UBound(TargetArray) - 1
        TargetArray(i) = TargetArray(i + 1)
    Next i

    '�Ō�̗v�f���폜����i�z����Ē�`�j
    ReDim Preserve TargetArray(UBound(TargetArray) - 1)
End Function

'***********************************************************
' �@�\   : 2�����z�񂩂猟���������L�[�ɕR�Â��l���擾
' ����   : �z��
' �߂�l : �z��
' �쐬��  : ����
'***********************************************************
Public Function GetItemFromList2D(arrayLst, keyCol, keyName, itemCol, Optional searchRow)
    If IsMissing(searchRow) Then
        searchRow = LBound(arrayLst)
    End If
    
    For i = searchRow To UBound(arrayLst)
        If arrayLst(i, keyCol) = keyName Then
            GetItemFromList2D = arrayLst(i, itemCol)
            If Not IsMissing(searchRow) Then searchRow = i
            Exit Function
        End If
    Next
End Function

'�z��̃T�C�Y������Ȃ��Ȃ������C�ɔz��T�C�Y���擾���Ēǉ�����
Function AddManyItemIntoLst(arrayLst As Variant, addItem) As Variant
    If IsArray(arrayLst) Then
        '�z��̍ŏI�s����z������擾����
        maxIndex = UBound(arrayLst)
        maxItem = arrayLst(maxIndex)
        If maxItem Like "lastIndex@*" Then
            '�ŏI�s�ɏ�񂠂�
            tmp = Split(maxItem, "@")
            lastIndex = tmp(1) + 1
            maxIndex = UBound(arrayLst)
        Else
            '�ŏI�s�ɏ��Ȃ�
            preMaxIndex = UBound(arrayLst)
            lastIndex = preMaxIndex + 1
            maxIndex = preMaxIndex + 1000
            ReDim Preserve arrayLst(maxIndex)
        End If
        arrayLst(maxIndex) = "lastIndex@" & lastIndex
        arrayLst(lastIndex) = addItem
    Else
        ReDim arrayLst(0)
        arrayLst(0) = addItem
    End If
End Function

'�z��̖����̋�s���폜����
Function EliminateBlankRowFromLst(arrayLst As Variant)
    maxIndex = UBound(arrayLst)
    maxItem = arrayLst(maxIndex)
    If maxItem Like "lastIndex@*" Then
        tmp = Split(maxItem, "@")
        lastIndex = tmp(1)
        ReDim Preserve arrayLst(lastIndex)
    End If
End Function

'UUID�𐶐�����
Public Function GetUUID() As String
    '(c) 2000 Gus Molina
    Dim udtGUID As GUID
    If (CoCreateGuid(udtGUID) = 0) Then
     GetUUID = _
      String(8 - Len(Hex$(udtGUID.Data1)), "0") & Hex$(udtGUID.Data1) & "-" & _
      String(4 - Len(Hex$(udtGUID.Data2)), "0") & Hex$(udtGUID.Data2) & "-" & _
      String(4 - Len(Hex$(udtGUID.Data3)), "0") & Hex$(udtGUID.Data3) & "-" & _
      IIf((udtGUID.Data4(0) < &H10), "0", "") & Hex$(udtGUID.Data4(0)) & _
      IIf((udtGUID.Data4(1) < &H10), "0", "") & Hex$(udtGUID.Data4(1)) & "-" & _
      IIf((udtGUID.Data4(2) < &H10), "0", "") & Hex$(udtGUID.Data4(2)) & _
      IIf((udtGUID.Data4(3) < &H10), "0", "") & Hex$(udtGUID.Data4(3)) & _
      IIf((udtGUID.Data4(4) < &H10), "0", "") & Hex$(udtGUID.Data4(4)) & _
      IIf((udtGUID.Data4(5) < &H10), "0", "") & Hex$(udtGUID.Data4(5)) & _
      IIf((udtGUID.Data4(6) < &H10), "0", "") & Hex$(udtGUID.Data4(6)) & _
      IIf((udtGUID.Data4(7) < &H10), "0", "") & Hex$(udtGUID.Data4(7))
    End If
End Function

'����������܂����񐔌�������
Function RepeatCombineStr(combineStr, repeatNum)
    For i = 1 To repeatNum
        resultStr = resultStr & combineStr
    Next

    RepeatCombineStr = resultStr
End Function

'***********************************************************
' �@�\   : 1�����z��̗v�f���폜
' ����   : �z��
' �߂�l : �z��
' �쐬��  : ����
'***********************************************************
Public Function ArrayRemove(ByRef TargetArray As Variant, ByVal deleteIndex)
    '�폜�������v�f�ȍ~�̗v�f��O�ɂ߂ď㏑���R�s�[
    For i = deleteIndex To UBound(TargetArray) - 1
        TargetArray(i) = TargetArray(i + 1)
    Next i

    '�Ō�̗v�f���폜����i�z����Ē�`�j
    ReDim Preserve TargetArray(UBound(TargetArray) - 1)
End Function

'***********************************************************
' �@�\   : �z��̌���
' ����   : �z��1, �z��2
' �߂�l : �z��
' �쐬��  : ����
'***********************************************************
Function CombineList(arrayLst1 As Variant, arrayLst2 As Variant)
    combineStr = Join(arrayLst1, vbCrLf) & vbCrLf & Join(arrayLst2, vbCrLf)
    CombineList = Split(combineStr, vbCrLf)
End Function

'***********************************************************
' �@�\   : �����l�̎擾
' ����   : �z��
' �쐬��  : ����
'***********************************************************
Function GetMedian(a_ar)
    Dim ar()                    '// �����z�񂩂琔�l�݂̂𒊏o�����z��
    Dim v                       '// �z��l
    Dim ret                     '// �߂�l
    Dim iHalf                   '// �z��v�f�̔���
    Dim iCount
    
    ReDim ar(0)
    
    '// ���l�ȊO������
    For Each v In a_ar
        '// ���l�̏ꍇ
        If (IsNumeric(v) = True And IsEmpty(v) = False) Then
            ar(UBound(ar)) = Val(v)
            ReDim Preserve ar(UBound(ar) + 1)
        End If
    Next
    
    '// �z��Ɋi�[�ς݂̏ꍇ
    If IsEmpty(ar(0)) = False Then
        '// �]���ȗ̈���폜
        ReDim Preserve ar(UBound(ar) - 1)
    End If
    
    '// �\�[�g
    Call QuickSort(ar)
    
    If IsEmpty(ar(0)) = True Then
        Set GetMedian = Nothing
        Exit Function
    End If
    
    iCount = UBound(ar)
    iHalf = Fix(iCount / 2)
    
    '// �����̏ꍇ
    If (iCount + 1) Mod 2 = 0 Then
        '// �z��̒����Q�̒l�̕���
        ret = (ar(iHalf) + ar(iHalf + 1)) / 2
    '// ��̏ꍇ
    Else
        '// �z��̒����̒l
        ret = ar(iHalf)
    End If
    
    GetMedian = ret
End Function

'2�̔z������ɕ��ׂČ�������
Function CombineColumns(arr1 As Variant, arr2 As Variant)
    If UBound(arr1) <> UBound(arr2) Then
        MsgBox "�z��̃T�C�Y����v���܂���"
        Stop
    End If
    
    Dim combiLst As Variant
    combiLst = arr1
    ReDim Preserve combiLst(UBound(arr1), UBound(arr1, 2) + UBound(arr2, 2) + 1)
    For i = LBound(arr2) To UBound(arr2)
        For j = LBound(arr2, 2) To UBound(arr2, 2)
            combiLst(i, UBound(arr1, 2) + j + 1) = arr2(i, j)
        Next
    Next

    CombineColumns = combiLst
End Function



