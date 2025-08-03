Attribute VB_Name = "共通ライブラリ"
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
' 機能   :　バブルソート2次元配列
' 目的   :  配列を並び替える
' 引数   :  ソートした配列
' 戻り値 :  なし
' 作成者  : 野島
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

'クイックソート
Sub QuickSort(a_ar, Optional iFirst As Long = 0, Optional iLast As Long = -1)
    Dim iLeft                   As Long      '// 左ループカウンタ
    Dim iRight                  As Long      '// 右ループカウンタ
    Dim sMedian                                 '// 中央値
    Dim tmp                                     '// 配列移動用バッファ
    
    '// ソート終了位置省略時は配列要素数を設定
    If (iLast = -1) Then
        iLast = UBound(a_ar)
    End If
    
    '// 中央値を取得
    sMedian = a_ar(Fix((iFirst + iLast) / 2))
    
    iLeft = iFirst
    iRight = iLast
    
    Do
        '// 中央値の左側をループ
        Do
            '// 配列の左側から中央値より大きい値を探す
            If (a_ar(iLeft) >= sMedian) Then
                Exit Do
            End If
            
            '// 左側を１つ右にずらす
            iLeft = iLeft + 1
        Loop
        
        '// 中央値の右側をループ
        Do
            '// 配列の右側から中央値より大きい値を探す
            If (sMedian >= a_ar(iRight)) Then
                Exit Do
            End If
            
            '// 右側を１つ左にずらす
            iRight = iRight - 1
        Loop
        
        '// 左側の方が大きければここで処理終了
        If (iLeft >= iRight) Then
            Exit Do
        End If
        
        '// 右側の方が大きい場合は、左右を入れ替える
        tmp = a_ar(iLeft)
        a_ar(iLeft) = a_ar(iRight)
        a_ar(iRight) = tmp
        
        '// 左側を１つ右にずらす
        iLeft = iLeft + 1
        '// 右側を１つ左にずらす
        iRight = iRight - 1
    Loop
    
    '// 中央値の左側を再帰でクイックソート
    If (iFirst < iLeft - 1) Then
        Call QuickSort(a_ar, iFirst, iLeft - 1)
    End If
    
    '// 中央値の右側を再帰でクイックソート
    If (iRight + 1 < iLast) Then
        Call QuickSort(a_ar, iRight + 1, iLast)
    End If
End Sub

'***********************************************************
' 機能   :　クイックソート2次元配列
' 目的   :  配列を並び替える
' 引数   :  ソートした配列
' 戻り値 :  なし
' 作成者  : 野島
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
' 機能   : ファイル保存処理(3次元配列)
' 引数   :  ArrayData:配列変数
'           filePath:ファイル保存場所
' 戻り値?､ : なし
' 作成者  : 野島
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
' 機能   : ファイル保存処理
' 引数   :  ArrayData:配列変数
'           filePath:ファイル保存場所
' 戻り値?､ : なし
' 作成者  : 野島
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
' 機能   : ファイル保存処理
' 引数   :  ArrayData:配列変数
'           filePath:ファイル保存場所
' 戻り値?､ : なし
' 作成者  : 野島
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
' 機能   : ファイル保存処理
' 引数   :  ArrayData:配列変数
'           filePath:ファイル保存場所
' 戻り値?､ : なし
' 作成者  : 野島
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
' 機能   : ファイル保存処理
' 引数   :  ArrayData:配列変数
'           filePath:ファイル保存場所
' 戻り値?､ : なし
' 作成者  : 野島
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
    MsgBox "下記のファイル保存内容にエラーが含まれています" & vbCrLf & "行数:" & i & vbCrLf & "列数:" & j & vbCrLf & "保存パス:" & filePath, vbCritical
    End
End Function

'***********************************************************
' 機能   : ファイル保存処理
' 引数   :  strText:変数
'           filePath:ファイル保存場所
' 戻り値?､ : なし
' 作成者  : 野島
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
' 機能   : ファイル保存処理
' 引数   :  strText:変数
'           filePath:ファイル保存場所
' 戻り値?､ : なし
' 作成者  : 野島
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
' 機能   : フォルダの作成
' 引数   : フォルダ名称（絶対パス）
' 戻り値 : なし
' 作成者  : 春山
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
' 機能   : 対象ディレクトリ下のサブディレクトリ下を含むファイルリスト取得
' 引数   : dirPath（対象ディレクトリの絶対パス）
' 戻り値?､ : ファイル名リスト（配列）
' 作成者  : 春山
'***********************************************************
Function MakeFilesList(Path As String, wildcard As String)
    Dim filenames() As String
    Dim buf As String, f As Object
    buf = Dir(Path & "\" & wildcard)
    
    Dim Cnt As Long: Cnt = 0
    '対象ディレクトリ階層のファイル名取得
    Do While buf <> ""
        Cnt = Cnt + 1
        ReDim Preserve filenames(Cnt)
        filenames(Cnt - 1) = Path & "\" & buf
        buf = Dir()
    Loop
    If Cnt = 0 Then
        ReDim Preserve filenames(0)
        'ディレクトリが存在しないとき用
        Dim buf2 As String
        buf2 = Dir(Path, vbDirectory)
        If buf2 = "" Then
            ReDim filenames(0)
            MakeFilesList = filenames
            Exit Function
        End If
    End If
    
    
    
    '対象ディレクトリのサブディレクトリ以下の階層のファイル名取得
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
' 機能   : CSV読込処理
' 引数   :
' 戻り値 : なし
' 作成者  : 佐藤
'***********************************************************
Function ReadCsv(ByVal File_Target As String)
'===========================================================================
'OpenステートメントのBinaryでの順次読み込みを行います
'===========================================================================
 
    Dim intFF As Long                           'ファイル番号
    Dim byt_buf() As Byte
    Dim var_buf
    Dim str_buf  As String                      'ただの汎用変数
    Dim str_Strings() As String                 'ファイルの中身全部の文字列型配列
    Dim row As Long                             '行数カウント
    Dim i As Long
     
    Dim bytSjis As String
    Dim str_Uni As String
    
    If Dir(File_Target) = "" Then Exit Function
          
    intFF = FreeFile
    Open File_Target For Binary As #intFF
        ReDim byt_buf(LOF(intFF))
        Get #intFF, , byt_buf
    Close #intFF
     
    str_Uni = StrConv(byt_buf(), vbUnicode) 'Unicodeに変換
     
    '==============================================================
    '配列化有効時
    If Right(str_Uni, 1) = vbNullChar Then strUni = Left(str_Uni, Len(str_Uni) - 1)
    var_buf = Split(str_Uni, vbCrLf) '改行コードごとに区切って配列化
    row = UBound(var_buf)            '行数取得
    If var_buf(row) Like vbNullChar Then
        ReDim Preserve var_buf(row - 1)
    End If
    '==============================================================
     
    ReadCsv = var_buf
End Function

'***********************************************************
' 機能   : CSV読込処理
' 引数   :
' 戻り値 : なし
' 作成者  : 佐藤
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
' 機能   : ログ保存処理（追記用）
' 引数   :  ArrayData:配列変数
'           filePath:ファイル保存場所
' 戻り値?､ : なし
' 作成者  : 佐藤
'***********************************************************
Sub outLog(DateTime As Date, outContent As String, ByRef fileDir As String)
    Dim filePath As String: filePath = fileDir & "\log" & Format(nowTime, "yyyymmddhhmm") & ".txt"
    
    Dim fileNumber As Long
    fileNumber = FreeFile
    
    Open filePath For Append As #fileNumber
    'ファイルが存在ダミー行
    If fileExist = "" Then
        Print #fileNumber, "Log No,Content"
    End If

    Print #fileNumber, Format(DateTime, "yy/mm/dd hh:mm") & "," & outContent & vbCrLf;
    Close #fileNumber
End Sub

Function CheckFileExist(filePath)
    Dim fileExist As String: fileExist = Dir(filePath)
    
    If fileExist = "" Then
        MsgBox "指定のファイルが見つかりません" & vbCrLf & filePath, vbCritical
        End
    End If
End Function

'全シートのフィルターをOFFにする
Function showAllData(WB As Workbook)
    Dim WS As Worksheet 'ワークシートのオブジェクト変数としてWSを定義'
    For Each WS In WB.Worksheets   'ブック内のワークシートの集合（Worksheets)からワークシートを1つずつWSに格納'
        If WS.FilterMode = True Then
            WS.showAllData
        End If
    Next WS
End Function

'***********************************************************
' 機能   : シートをファイルへ書き込む
' 戻り値?､ : なし
' 作成者  : 佐藤
'***********************************************************

Sub SaveSheet(stName, savePath)
    With ThisWorkbook.Worksheets(stName)
    
    lastRow = .Range("A1").SpecialCells(xlLastCell).row
    lastCol = .Range("A1").SpecialCells(xlLastCell).Column
        
    saveRange = .Range(.Cells(1, 1), .Cells(lastRow, lastCol))
    
    If Dir(savePath) <> "" Then
        msgResult = MsgBox("ファイルが存在しますが上書きますか", Buttons:=vbYesNo)
        
        If msgResult = vbYes Then
            Call OutputText(saveRange, CStr(savePath))
        Else
            End
        End If
    Else
        Call OutputText(saveRange, CStr(savePath))
    End If
    
    End With
    
    MsgBox "保存しました", vbInformation
End Sub


'***********************************************************
' 機能   : ファイルをシートに読み込む
' 引数   :
' 戻り値?､ : なし
' 作成者  : 佐藤
'***********************************************************

Sub ReadSheet(stName, savePath)
    With ThisWorkbook.Worksheets(stName)
    
    csvLst = ReadCsv(savePath)
    csvLst = ConvertDimensionToSplitComma(csvLst)
        
    .Cells.ClearContents
    .Range(.Cells(1, 1), .Cells(UBound(csvLst, 1), UBound(csvLst, 2))) = csvLst
    End With
    
    MsgBox "読込みました", vbInformation
End Sub

'***********************************************************
' 機能   : ブックを開いているかどうか判定
' 引数   : なし
' 戻り値 : なし
'***********************************************************
Function IsBookOpened(a_sFilePath) As Boolean
    On Error Resume Next
    
    '// 保存済みのブックか判定
    Open a_sFilePath For Append As #1
    Close #1
    
    If Err.Number > 0 Then
        '// 既に開かれている場合
        IsBookOpened = True
    Else
        '// 開かれていない場合
        IsBookOpened = False
    End If
End Function

'***********************************************************
' 機能   : 共有ブックを開いているかどうか判定
' 引数   : なし
' 戻り値 : なし
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
' 機能   : 共有ブックを開いているかどうか判定
' 引数   : なし
' 戻り値 : なし
'***********************************************************
Function CheckFileOpened(filePath)
    If Dir(filePath) <> "" Then
        If IsBookOpened(filePath) Then
            MsgBox "出力ファイルが開かれているため閉じてください" & vbCrLf & filePath, vbCritical
            End
        End If
    End If
End Function

'***********************************************************
' 機能   : 1文字ずつに配列に分割する
' 引数   : なし
' 戻り値 : なし
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
' 機能   : 1次元配列を2次元配列に変換
' 引数   : なし
' 戻り値 : なし
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
' 機能   : カンマで区切られた1次元配列を2次元配列に変換
' 引数   : なし
' 戻り値 : なし
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
' 機能   : カンマで区切られた1次元配列を2次元配列に変換　※配列インデックスの開始は0
' 引数   : なし
' 戻り値 : なし
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
' 機能   : 2次元配列を1次元配列に変換
' 引数   : なし
' 戻り値 : なし
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
' 機能   : ファイル保存処理
' 引数   :  ArrayData:配列変数
'           filePath:ファイル保存場所
' 戻り値?､ : なし
' 作成者  : 佐藤
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
    
    ' バッファを Flush してファイルを閉じる
    outputFile.Close
    Set fso = Nothing
End Sub


'***********************************************************
' 機能   : 処理速度計測
' 引数   :  処理速度保存変数
'           前回打刻時刻
' 戻り値?､ : なし
' 作成者  : 佐藤
'***********************************************************
Function CalcProcessSpeed(ByRef saveTime As Double)
    nowProcessTime = Timer
    
    '処理速度を保存
    If mileStoneTime <> 0 Then
        saveTime = saveTime + nowProcessTime - mileStoneTime
    End If
    
    'マイルストーンの時刻を更新
    mileStoneTime = nowProcessTime
End Function

'***********************************************************
' 機能   : 組み合わせの取得
' 引数   : 候補の配列
'          組み合わせ数
' 戻り値､ : 組み合わせ結果の二次元配列
' 作成者  : 佐藤
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
  
    '入力配列から指定数を取り出す
    'まずは、1,2,3,4,5を作成
    ReDim aryTemp(UBound(aryIn))
    For i1 = 0 To UBound(aryIn)
        aryTemp(i1) = i1
    Next
    '1,2,3,4,5の順列作成
    Call permutation(aryTemp, aryNum1)
    '1,2,3,4,5の順列から先頭の指定数を取り出す
    'ここは組み合わせを作りたいので順序違いも省く
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
  
    '入力配列の組み合わせに戻す
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
            '配列を入れ替える
            ary = aryIn
            sTemp = aryIn(i)
            aryIn(i) = aryIn(j)
            aryIn(j) = sTemp
            '再帰処理、開始位置を+1
            Call permutation(aryIn, aryOut, i + 1)
            aryIn = ary '配列を元に戻す
        Next
    Else
        '配列の最後まで行ったので出力
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
                  ByRef TargetArray As Variant) As Long    '……(1)'
  If Not IsArray(TargetArray) _
    Then getArrayDimension = False: Exit Function    '……(2)'
  Dim n As Long    '……(3)'
  n = 0
  Dim tmp As Long
  On Error Resume Next    '……(4)'
  Do While Err.Number = 0
    n = n + 1
    tmp = UBound(TargetArray, n)
  Loop
  Err.Clear
  getArrayDimension = n - 1    '……(5)'
End Function

'***********************************************************
' 機能   : コマンドプロンプト実行処理
' 引数   :  コマンド
' 戻り値 : なし
' 作成者  : 佐藤
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
' 機能   : コミット番号の取得
' 引数   : ファイルパス
' 戻り値 : コミット番号
' 作成者  : 佐藤
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
        MsgBox "コミット番号の取得に失敗しました" & vbCrLf & commitNum
        End
    End If
    GetCommitNum = commitNum
End Function

'***********************************************************
' 機能   : コミットする
' 引数   : ファイルパス
' 戻り値 : コミット番号
' 作成者  : 佐藤
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
' 機能   : 1次元配列の重複削除
' 引数   : 配列
' 戻り値 : 重複を削除した配列
' 作成者  : 佐藤
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
' 機能   : 2次元配列から指定した列を取得
' 引数   : 2次元配列、指定列
' 戻り値 : 1列のみの2次元配列
' 作成者  : 佐藤
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
' 機能   : 2次元配列の行列変換処理
' 引数   : 2次元配列
' 戻り値 : 行列変換した2次元配列
' 作成者  : 佐藤
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
' 機能   : 1次元配列の行追加処理
' 引数   : 1次元配列、追加テキスト
' 戻り値 : 行追加した1次元配列
' 作成者  : 佐藤
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
' 機能   : 同じ文字を指定数並べた文字列を作る
' 引数   : 文字、繰り返し数
' 戻り値 : 結合した文字列
' 作成者  : 佐藤
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
' 機能   : 2次元配列を2次元Collectionに変換する
' 引数   : 2次元配列
' 戻り値 : 2次元Collection
' 作成者  : 佐藤
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
' 機能   : 2次元Collectionを2次元配列に変換する
' 引数   : 2次元Collection
' 戻り値 : 2次元配列
' 作成者  : 佐藤
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
' 機能   : 2次元配列の特定行に2次元Collectionの特定行を代入する
' 引数   : 2次元Collection、2次元配列、特定行
' 戻り値 : 2次元配列
' 作成者  : 佐藤
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
' 機能   : OFFの行を省く
' 引数   : 2次元配列
' 戻り値 :
' 作成者  : 佐藤
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
' 機能   : 配列の読込
' 引数   : シート名、配列の取得開始行、配列の取得列数を決めるカラム行
' 戻り値 : 取り込んだ2次元配列
' 作成者  : 佐藤
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

'マージソート昇順
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

'マージソート降順
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

'指標名小文字変換処理除去
Function AddSmallChar(indexName)
    If Left(indexName, 2) = "ZZ" Then
        AddSmallChar = "0" & indexName
        Exit Function
    End If

    Dim reg
    Set reg = CreateObject("VBScript.RegExp")
     
    '正規表現の指定
    With reg
        .pattern = "^[A-Z][A-Z][0-9]{3}"       'パターンを指定
        .IgnoreCase = False '大文字と小文字を区別するか(False)、しないか(True)
    End With
    
    If reg.test(indexName) Then
        AddSmallChar = indexName
        Exit Function
    End If
    
    With reg
        .pattern = "^[a-z][A-Z][0-9]{3}"       'パターンを指定
        .IgnoreCase = False '大文字と小文字を区別するか(False)、しないか(True)
    End With
    
    If reg.test(indexName) Then
        AddSmallChar = "s" & indexName
        Exit Function
    End If
    
    With reg
        .pattern = "^[A-Z][a-z][0-9]{3}"       'パターンを指定
        .IgnoreCase = False '大文字と小文字を区別するか(False)、しないか(True)
    End With
    
    If reg.test(indexName) Then
        AddSmallChar = Left(indexName, 1) & "s" & Right(indexName, 4)
        Exit Function
    End If
    
    With reg
        .pattern = "^[a-z][a-z][0-9]{3}"       'パターンを指定
        .IgnoreCase = False '大文字と小文字を区別するか(False)、しないか(True)
    End With
    
    If reg.test(indexName) Then
        AddSmallChar = "s" & Left(indexName, 1) & "s" & Right(indexName, 4)
        Exit Function
    End If
    
    MsgBox "Error"
End Function

'3つの中で最大の数値配列番号を返す
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

'配列を拡張してデータを入れる
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

'配列をコレクションに変換
Function ConvertListToCollection(a As Variant) As Collection
    Dim c As New Collection
    For Each Item In a
      c.Add Item, Item
    Next Item
    Set ConvertListToCollection = c
End Function

'コレクションを配列に変換
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
' 機能   : 2次元配列の重複チェック
' 引数   : 配列
' 戻り値 : True/False
' 作成者  : 佐藤
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
' 機能   : 配列からヘッダーを落とす
' 引数   : 配列
' 戻り値 : 配列
' 作成者  : 佐藤
'***********************************************************
Function RemoveHeaderFromLst(arrayLst As Variant, headerCount)
    If UBound(arrayLst) < headerCount Then
        MsgBox "配列数より削除するヘッダー行の方が大きいです"
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
' 機能   : 1次元配列の要素を削除
' 引数   : 配列
' 戻り値 : 配列
' 作成者  : 佐藤
'***********************************************************
Public Function RemoveItemFromArray(ByRef TargetArray As Variant, ByVal deleteIndex)
'    uniqueStr = "@#$"
'    TargetArray(deleteIndex) = uniqueStr
'    arrayStr = Join(TargetArray, ",")
'    arrayStr = Replace(arrayStr, "," & uniqueStr, "")
'
'    TargetArray = Split(arrayStr, ",")

    '削除したい要素以降の要素を前につめて上書きコピー
    For i = deleteIndex To UBound(TargetArray) - 1
        TargetArray(i) = TargetArray(i + 1)
    Next i

    '最後の要素を削除する（配列を再定義）
    ReDim Preserve TargetArray(UBound(TargetArray) - 1)
End Function

'***********************************************************
' 機能   : 2次元配列から検索したいキーに紐づく値を取得
' 引数   : 配列
' 戻り値 : 配列
' 作成者  : 佐藤
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

'配列のサイズが足りなくなったら一気に配列サイズを取得して追加する
Function AddManyItemIntoLst(arrayLst As Variant, addItem) As Variant
    If IsArray(arrayLst) Then
        '配列の最終行から配列情報を取得する
        maxIndex = UBound(arrayLst)
        maxItem = arrayLst(maxIndex)
        If maxItem Like "lastIndex@*" Then
            '最終行に情報あり
            tmp = Split(maxItem, "@")
            lastIndex = tmp(1) + 1
            maxIndex = UBound(arrayLst)
        Else
            '最終行に情報なし
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

'配列の末尾の空行を削除する
Function EliminateBlankRowFromLst(arrayLst As Variant)
    maxIndex = UBound(arrayLst)
    maxItem = arrayLst(maxIndex)
    If maxItem Like "lastIndex@*" Then
        tmp = Split(maxItem, "@")
        lastIndex = tmp(1)
        ReDim Preserve arrayLst(lastIndex)
    End If
End Function

'UUIDを生成する
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

'文字列を決まった回数結合する
Function RepeatCombineStr(combineStr, repeatNum)
    For i = 1 To repeatNum
        resultStr = resultStr & combineStr
    Next

    RepeatCombineStr = resultStr
End Function

'***********************************************************
' 機能   : 1次元配列の要素を削除
' 引数   : 配列
' 戻り値 : 配列
' 作成者  : 佐藤
'***********************************************************
Public Function ArrayRemove(ByRef TargetArray As Variant, ByVal deleteIndex)
    '削除したい要素以降の要素を前につめて上書きコピー
    For i = deleteIndex To UBound(TargetArray) - 1
        TargetArray(i) = TargetArray(i + 1)
    Next i

    '最後の要素を削除する（配列を再定義）
    ReDim Preserve TargetArray(UBound(TargetArray) - 1)
End Function

'***********************************************************
' 機能   : 配列の結合
' 引数   : 配列1, 配列2
' 戻り値 : 配列
' 作成者  : 佐藤
'***********************************************************
Function CombineList(arrayLst1 As Variant, arrayLst2 As Variant)
    combineStr = Join(arrayLst1, vbCrLf) & vbCrLf & Join(arrayLst2, vbCrLf)
    CombineList = Split(combineStr, vbCrLf)
End Function

'***********************************************************
' 機能   : 中央値の取得
' 引数   : 配列
' 作成者  : 佐藤
'***********************************************************
Function GetMedian(a_ar)
    Dim ar()                    '// 引数配列から数値のみを抽出した配列
    Dim v                       '// 配列値
    Dim ret                     '// 戻り値
    Dim iHalf                   '// 配列要素の半分
    Dim iCount
    
    ReDim ar(0)
    
    '// 数値以外を除去
    For Each v In a_ar
        '// 数値の場合
        If (IsNumeric(v) = True And IsEmpty(v) = False) Then
            ar(UBound(ar)) = Val(v)
            ReDim Preserve ar(UBound(ar) + 1)
        End If
    Next
    
    '// 配列に格納済みの場合
    If IsEmpty(ar(0)) = False Then
        '// 余分な領域を削除
        ReDim Preserve ar(UBound(ar) - 1)
    End If
    
    '// ソート
    Call QuickSort(ar)
    
    If IsEmpty(ar(0)) = True Then
        Set GetMedian = Nothing
        Exit Function
    End If
    
    iCount = UBound(ar)
    iHalf = Fix(iCount / 2)
    
    '// 偶数の場合
    If (iCount + 1) Mod 2 = 0 Then
        '// 配列の中央２つの値の平均
        ret = (ar(iHalf) + ar(iHalf + 1)) / 2
    '// 奇数の場合
    Else
        '// 配列の中央の値
        ret = ar(iHalf)
    End If
    
    GetMedian = ret
End Function

'2つの配列を横に並べて結合する
Function CombineColumns(arr1 As Variant, arr2 As Variant)
    If UBound(arr1) <> UBound(arr2) Then
        MsgBox "配列のサイズが一致しません"
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



