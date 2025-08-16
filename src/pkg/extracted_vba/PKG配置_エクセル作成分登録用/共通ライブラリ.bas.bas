Attribute VB_Name = "共通ライブラリ"
'104    ←バージョン情報(整数3桁) ※このバージョンによりModule自動更新が判断される

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
Sub QuickSort(a_Ar, Optional iFirst As Long = 0, Optional iLast As Long = -1)
    Dim iLeft                   As Long      '// 左ループカウンタ
    Dim iRight                  As Long      '// 右ループカウンタ
    Dim sMedian                                 '// 中央値
    Dim tmp                                     '// 配列移動用バッファ
    
    '// ソート終了位置省略時は配列要素数を設定
    If (iLast = -1) Then
        iLast = UBound(a_Ar)
    End If
    
    '// 中央値を取得
    sMedian = a_Ar(Fix((iFirst + iLast) / 2))
    
    iLeft = iFirst
    iRight = iLast
    
    Do
        '// 中央値の左側をループ
        Do
            '// 配列の左側から中央値より大きい値を探す
            If (a_Ar(iLeft) >= sMedian) Then
                Exit Do
            End If
            
            '// 左側を１つ右にずらす
            iLeft = iLeft + 1
        Loop
        
        '// 中央値の右側をループ
        Do
            '// 配列の右側から中央値より大きい値を探す
            If (sMedian >= a_Ar(iRight)) Then
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
        tmp = a_Ar(iLeft)
        a_Ar(iLeft) = a_Ar(iRight)
        a_Ar(iRight) = tmp
        
        '// 左側を１つ右にずらす
        iLeft = iLeft + 1
        '// 右側を１つ左にずらす
        iRight = iRight - 1
    Loop
    
    '// 中央値の左側を再帰でクイックソート
    If (iFirst < iLeft - 1) Then
        Call QuickSort(a_Ar, iFirst, iLeft - 1)
    End If
    
    '// 中央値の右側を再帰でクイックソート
    If (iRight + 1 < iLast) Then
        Call QuickSort(a_Ar, iRight + 1, iLast)
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
Sub AppendSingleText(strText, filePath As String, Optional onoffSwitch As String = "ON")
    If onoffSwitch = "ON" Then
        Call MakeFolder(filePath)
        
        Dim i As Long
                
        Dim fileNumber As Long
        fileNumber = FreeFile
        
        Open filePath For Append As #fileNumber
                    
        Print #fileNumber, strText;
        Print #fileNumber, vbCrLf;
        
        Close #fileNumber
    End If
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
Function readCsv(ByVal File_Target As String)
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
          
    intFF = FreeFile
    Open File_Target For Binary As #intFF
        ReDim byt_buf(LOF(intFF))
        Get #intFF, , byt_buf
    Close #intFF
     
    str_Uni = StrConv(byt_buf(), vbUnicode) 'Unicodeに変換
     
    '==============================================================
    '配列化有効時
    var_buf = Split(str_Uni, vbCrLf) '改行コードごとに区切って配列化
    'Row = UBound(var_buf)            '行数取得
    '==============================================================
     
    readCsv = var_buf
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
    
    csvLst = readCsv(savePath)
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
Function ConvertDimensionToSplitComma(arrayLst)
  Dim newLst As Variant
  minRow = LBound(arrayLst)
  maxRow = UBound(arrayLst)
  If minRow = 0 Then
    minRow = minRow + 1
    maxRow = maxRow + 1
    ReDim Preserve arrayLst(1 To maxRow)
  End If
  tmp = Split(arrayLst(minRow), ",")
  maxCol = UBound(tmp) + 1
  ReDim newLst(1 To maxRow, 1 To maxCol)
  
  For i = LBound(arrayLst) To UBound(arrayLst)
    arrayRowLst = Split(arrayLst(i), ",")
    For j = LBound(arrayRowLst) To UBound(arrayRowLst)
        newLst(i, j + 1) = arrayRowLst(j)
    Next j
  Next i
  
  ConvertDimensionToSplitComma = newLst
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
    maxCol = UBound(arrayLst, 2)
    ReDim newLst(minRow To maxRow)
  
    For i = minRow To maxRow
        For j = minCol To maxCol
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
    Dim FSO
    Set FSO = CreateObject("Scripting.FileSystemObject")
        
    Dim outputFile
    
    If Dir(filePath) = "" Then
        Call MakeFolder(CStr(filePath))
        Set outputFile = FSO.OpenTextFile(filePath, 2, True)
        outputFile.Write (headerText)
        outputFile.Write (vbCrLf)
        outputFile.Close
    End If
    Set outputFile = FSO.OpenTextFile(filePath, 8, False)
        
    outputFile.Write (outText)
    outputFile.Write (vbCrLf)
    
    ' バッファを Flush してファイルを閉じる
    outputFile.Close
    Set FSO = Nothing
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
                  ByRef targetArray As Variant) As Long    '……(1)'
  If Not IsArray(targetArray) _
    Then getArrayDimension = False: Exit Function    '……(2)'
  Dim n As Long    '……(3)'
  n = 0
  Dim tmp As Long
  On Error Resume Next    '……(4)'
  Do While Err.Number = 0
    n = n + 1
    tmp = UBound(targetArray, n)
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
    Dim FSO As Object
    Set FSO = CreateObject("Scripting.FileSystemObject")
    fileName = FSO.GetFileName(filePath)
    folderPath = FSO.GetParentFolderName(filePath)
      
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
    Dim FSO As Object
    Set FSO = CreateObject("Scripting.FileSystemObject")
    fileName = FSO.GetFileName(filePath)
    folderPath = FSO.GetParentFolderName(filePath)
      
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
        maxIndex = checkDuplicateDic.count - 1
        ReDim newArrayLst(maxIndex)
        count = 0
        For Each rowValue In checkDuplicateDic
            newArrayLst(count) = rowValue
            count = count + 1
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
    maxCol = UBound(arrayLst)
    minRow = LBound(arrayLst, 2)
    minCol = LBound(arrayLst)
    
    Dim newArrayLst As Variant
    ReDim newArrayLst(minRow To maxRow, minCol To maxCol)
    
    For i = minRow To maxRow
        For j = minCol To maxCol
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
    maxRow = myCol.count
    ReDim newArray(1 To maxRow, 1 To 1)
    
    For i = 1 To myCol.count
        Set rowCol = myCol(i)
        maxColumn = rowCol.count
        ReDim Preserve newArray(1 To maxRow, 1 To maxColumn)
        For j = 1 To rowCol.count
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
    
    For i = 1 To UBound(myLst, 2)
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
    
    For i = 1 To collection2d.count - 1
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
        lastRow = .Cells(Rows.count, 1).End(xlUp).row
        lastCol = .Cells(columnSizeRow, 1).End(xlToRight).Column
                
        TakeArrayFromSheet = .Range(.Cells(startRow, 1), .Cells(lastRow, lastCol))
    End With

End Function

