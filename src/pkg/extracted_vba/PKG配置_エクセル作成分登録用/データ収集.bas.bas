Attribute VB_Name = "データ収集"
Const stReadPkg = "PKG読込"
Const stHelpInput = "入力補助"
Const stDataFolder = "データフォルダ指定"
Const stFolder = "対象とフォルダ"

Const lsFileName = "Logic_Signal_"
Const rnvFileHead = "realtime_nesl_value_"

Const mainTimeCol = 1
Const mainStartCol = 2

Const mainLabelRow = 7
Const mainStartRow = 8

Const startConCol = 1
Const conTargetCol = 0
Const conNameCol = 1

Const histDateCol = 1
Const histTimeCol = 2

Public Const dataKubunCol = 1
Public Const dataPairCol = 2
Public Const dataAshiCol = 3
Public Const dataAshiCountCol = 4
Public Const dataHistCol = 5
Public Const dataIndexPriceCol = 6
Public Const dataUpDownCol = 7
Public Const dataPkgCol = 8

Dim resultFileHead As String
Dim startDate As Date
Dim endDate As Date
Dim timeSeriesLst As Variant
Dim timeSeriesLstInDay As Variant
Dim readDataDic As Variant
Dim targetFolderDic As Variant
Dim historicalDir As String
Dim meanVal As Long
Dim mainLastCol As Long
Dim readPkgLst As Variant
Dim dataFolderLst As Variant
Dim targetDateDic As Variant
Dim histLst As Variant
Dim outCharType As String
Dim dayAshiCountDic As Variant

Sub GatherData()
    Application.ScreenUpdating = False
    Application.Calculation = xlCalculationManual
    
    Call initialize
    
    Dim pasteRow As Long: pasteRow = mainStartRow
    For Each targetDate In targetDateDic
        Call UpdateTimeSeriesLst(CDate(targetDate))
        For i = LBound(readPkgLst, 2) To UBound(readPkgLst, 2)
            Dim pasteLst As Variant
            readCondition = readPkgLst(1, i)
            If readCondition Like "*^*" Then
                tmp = Split(readCondition, "^")
                Dim conTarget As String: conTarget = tmp(0)
                Dim conName As String: conName = tmp(1)
                
                If conName Like "[A-Z][A-Z]###" Or _
                    conName Like "s[a-z][A-Z]###" Or _
                    conName Like "[A-Z]s[a-z]###" Or _
                    conName Like "s[a-z]s[a-z]###" Then
                    pasteLst = getNeslPrice(conTarget, conName, rnvFileHead & Format(targetDate, "yyyymmdd") & ".csv", i + 1)
                Else
                    pasteLst = getTimeSeriesData(conTarget, conName, lsFileName & Format(targetDate, "yymmdd") & ".csv", i + 1)
                End If
            Else
                MsgBox "入力形式が正しくありません" & vbCrLf & readCondition, vbCritical
                End
            End If
            Call PasteData(pasteRow, pasteLst, i + 1, dayAshiCountDic)
        Next
            
        ashiCount = UBound(timeSeriesLstInDay)
        pasteRow = pasteRow + ashiCount
    Next
    
    Application.ScreenUpdating = True
    'Application.Calculation = xlCalculationAutomatic
    Application.StatusBar = False
    MsgBox "Finished!"
End Sub

Function initialize()
    Set readDataDic = CreateObject("Scripting.Dictionary")
    Set targetFolderDic = CreateObject("Scripting.Dictionary")
    Set dayAshiCountDic = CreateObject("Scripting.Dictionary")
    Call AutoFilterOff
                                
    With ThisWorkbook.Worksheets(stDataFolder)
        lastRow = .Cells(Rows.count, 1).End(xlUp).row
        lastCol = .Cells(1, 1).End(xlToRight).Column
        
        dataFolderLabel = .Range(.Cells(1, 1), .Cells(lastRow, lastCol))
        dataFolderLst = .Range(.Cells(2, 1), .Cells(lastRow, lastCol))
    End With
                
    With ThisWorkbook.Worksheets(stFolder)
        lastRow = .Cells(Rows.count, 1).End(xlUp).row
        lastCol = .Cells(1, 1).End(xlToRight).Column
        folderLst = .Range(.Cells(2, 1), .Cells(lastRow, lastCol))
        
        For i = LBound(folderLst) To UBound(folderLst)
            targetType = folderLst(i, 1)
            Select Case targetType
                Case "通貨"
                    targetType = "PAIR"
                Case "時間足"
                    targetType = "PERIOD"
                Case "期間"
                    targetType = "TERM"
            End Select
            
            targetValue = folderLst(i, 2)
            folderName = folderLst(i, 3)
            
            targetFolderDic.Add targetType & targetValue, folderName
        Next i
    End With
End Function


Function GetTimeSeriesLst()
    'ヒストリカルの読込
    nextDate = DateAdd("d", 1, endDate)
    histPath = GetDataFolder("HISTORICAL", meanVal & "91")
    histLst = GetHistoricalLst(CStr(histPath), startDate, "yyyy.")
    
    Dim timeSeriesLst As Variant
    ReDim timeSeriesLst(0)
    maxIndex = 0
    
    For i = LBound(histLst) To UBound(histLst)
        If Len(histLst(i, histDateCol)) > 1 Then
            histDate = CDate(Replace(histLst(i, histDateCol), ".", "/"))
            histTime = CDate(histLst(i, histTimeCol))
            histDateTime = histDate + histTime
            
            If histDateTime >= startDate And histDateTime < nextDate Then
                ReDim Preserve timeSeriesLst(maxIndex)
                timeSeriesLst(maxIndex) = histDateTime
                maxIndex = UBound(timeSeriesLst) + 1
            End If
        End If
    Next i
    
    Set targetDateDic = CreateObject("Scripting.Dictionary")
    For i = LBound(timeSeriesLst) To UBound(timeSeriesLst)
        targetDate = FormatDateTime(timeSeriesLst(i), vbShortDate)
        If Not targetDateDic.exists(targetDate) Then
            targetDateDic.Add targetDate, 1
        End If
    Next i
    timeSeriesLst = ConvertDimensionToSplitComma(timeSeriesLst)
        
    With ThisWorkbook.Worksheets(stReadPkg)
    
    .Range(.Cells(mainStartRow, 1), .Cells(Rows.count, 1)).ClearContents
    .Range(.Cells(mainStartRow, 1), .Cells(mainStartRow - 1 + UBound(timeSeriesLst), 1)) = timeSeriesLst
    
    If outCharType = "文字列型" Then
        .Range(.Cells(mainStartRow, 2), .Cells(mainStartRow - 1 + UBound(timeSeriesLst), Columns.count)).NumberFormatLocal = "@"
    Else
        .Range(.Cells(mainStartRow, 2), .Cells(mainStartRow - 1 + UBound(timeSeriesLst), Columns.count)).NumberFormatLocal = "G/標準"
    End If
    
    End With
    
    histLst = ConvertDimension2Dto1D(histLst)
End Function

Function UpdateTimeSeriesLst(targetDate As Date)
    filterValue = Format(targetDate, "yyyy.mm.dd")
    filterLst = Filter(histLst, filterValue)
    filterLst = ConvertDimensionToSplitComma(filterLst)
    timeSeriesLstInDay = filterLst
End Function

'時系列データの取得
Function GetHistoricalLst(filePath As String, targetDate As Date, filterFormat As String)
    histFullLst = readCsv(filePath)
    filterValue = Format(targetDate, filterFormat)
    filterLst = Filter(histFullLst, filterValue)
    filterLst = ConvertDimensionToSplitComma(filterLst)
    GetHistoricalLst = filterLst
End Function


'// オートフィルタ解除関数
Sub AutoFilterOff()
    With ThisWorkbook.Worksheets(stReadPkg)
    
    '// オートフィルタが解除されている場合
    If (.AutoFilterMode = False) Then
        Exit Sub
    End If
    
    .Range(mainLabelRow & ":" & mainLabelRow).AutoFilter
    .Range(mainLabelRow & ":" & mainLabelRow).AutoFilter

    End With
End Sub
    
'必要な時系列データを取得する。必要に応じてファイルからExcelシート上に保持する
Function getTimeSeriesData(conTarget As String, pkgNum As String, fileName As String, targetCol As Long)
    Dim timeSeriesDataLst As Variant
    
    absTarget = Left(conTarget, 1) + meanVal - 1 & Right(conTarget, 2)
    Dim filePath As String: filePath = GetDataFolder("PKG", absTarget, pkgNum) & "\" & fileName
    If Dir(filePath) = "" Then
    
    Else
        tmp = readCsv(filePath)
        
        If Left(conTarget, 1) > 1 Then
            '先足系のPKGの場合は、データの時刻間隔を調整する
            tmp = AdjustTimeInterval(timeSeriesLstInDay, tmp)
        End If
        
        maxRow = UBound(timeSeriesLstInDay)
        ReDim timeSeriesDataLst(1 To maxRow, 0)
        For i = 1 To maxRow
            buf = Split(tmp(i), ",")
            code = buf(1)
            timeSeriesDataLst(i, 0) = code
        Next i
        getTimeSeriesData = timeSeriesDataLst
    End If
End Function

'指標の価格リストから価格を取得
Function getNeslPrice(conTarget As String, targetLineName As String, fileName As String, targetCol As Long)
    Dim timeSeriesDataLst As Variant
    
    absTarget = Left(conTarget, 1) + meanVal - 1 & Right(conTarget, 2)
    neslDir = GetDataFolder("INDEXPRICE", absTarget)
    If targetLineName Like "ZZ*" Then
        'フォルダの並び順の都合上ZZ系の指標のみ頭に0がついている
        targetLineName = "0" & targetLineName
    End If
    filePath = neslDir & "\" & targetLineName & "\" & fileName
    
    If Dir(filePath) = "" Then
    
    Else
        tmp = readCsv(filePath)
        
        If Left(conTarget, 1) > 1 Then
            '先足系のPKGの場合は、データの時刻間隔を調整する
            tmp = AdjustTimeInterval(timeSeriesLstInDay, tmp)
        End If
        
        maxRow = UBound(timeSeriesLstInDay)
        ReDim timeSeriesDataLst(1 To maxRow, 0)
        For i = 1 To maxRow
            buf = Split(tmp(i), ",")
            code = buf(1)
            timeSeriesDataLst(i, 0) = code
        Next i
        getNeslPrice = timeSeriesDataLst
    End If
End Function

'先足データを今足の時系列の間隔にそろえる
Function AdjustTimeInterval(imaAshiLst As Variant, sakiAshiLst As Variant)
    '初期状態取得
    adjustLst = Array("Time,Price")
    sakiAshiRowLst = Split(sakiAshiLst(1), ",")
    indexState = sakiAshiRowLst(1)
    If Len(sakiAshiLst(2)) > 1 Then
        nextRowLst = Split(sakiAshiLst(2), ",")
        nextIndexDateTime = CDate(nextRowLst(0))
    End If
    targetIndex = 2
    
    For i = LBound(imaAshiLst) To UBound(imaAshiLst)
        If imaAshiLst(i, LBound(imaAshiLst, 2)) <> "" Then
            tmpDate = Replace(imaAshiLst(i, 1), ".", "/") & " " & imaAshiLst(i, 2)
            timeSeriesDateTime = CDate(tmpDate)
            
            '時刻がきたら値をアップデートする
            If nextIndexDateTime = timeSeriesDateTime Then
                sakiAshiRowLst = Split(sakiAshiLst(targetIndex), ",")
                indexState = sakiAshiRowLst(1)
                If Len(sakiAshiLst(targetIndex + 1)) > 1 Then
                    nextRowLst = Split(sakiAshiLst(targetIndex + 1), ",")
                    nextIndexDateTime = CDate(nextRowLst(0))
                End If
                targetIndex = targetIndex + 1
            End If
                    
            If IsArray(adjustLst) Then
                adjustLst = Split(Join(adjustLst, vbCrLf) & vbCrLf & timeSeriesDateTime & "," & indexState, vbCrLf)
            End If
        End If
    Next
    
    AdjustTimeInterval = adjustLst
End Function

Function PasteData(pasteRow, pasteLst As Variant, targetCol, dayAshiCountDic As Variant)
    With ThisWorkbook.Worksheets(stReadPkg)
    
    If IsArray(pasteLst) Then
        .Range(.Cells(pasteRow, targetCol), .Cells(UBound(pasteLst, 1) + pasteRow - 1, targetCol)) = pasteLst
    Else
        .Cells(pasteRow, targetCol) = "NO FILE"
    End If
    
    End With
End Function

Function GetDataFolder(dataType, target, Optional pkgNum) As String
    targetPeriod = Left(target, 1)
    targetTerm = Mid(target, 2, 1)
    targetPair = Right(target, 1)
    
    For i = LBound(dataFolderLst) To UBound(dataFolderLst)
        If CStr(dataFolderLst(i, dataPairCol)) = targetPair Then
            If CStr(dataFolderLst(i, dataAshiCol)) = targetPeriod Then
                Select Case dataType
                Case "HISTORICAL"
                    GetDataFolder = dataFolderLst(i, dataHistCol)
                Case "INDEXPRICE"
                    GetDataFolder = dataFolderLst(i, dataIndexPriceCol)
                Case "UPDOWN"
                    GetDataFolder = dataFolderLst(i, dataUpDownCol)
                Case "PKG"
                    pkgPath = dataFolderLst(i, dataPkgCol)
                    termName = targetFolderDic.item("TERM" & targetTerm)
                    pkgPath = Replace(pkgPath, "<周期>", termName)
                    pkgPath = Replace(pkgPath, "<PKG>", pkgNum)
                    GetDataFolder = pkgPath
                End Select
                Exit For
            End If
        End If
    Next i
    
    If GetDataFolder = "" Then
        MsgBox "対象のフォルダがみつかりません" & vbCrLf & "対象:" & target & vbCrLf & "データタイプ:" & dataType, vbCritical
        End
    End If
End Function

Sub ConvertCondition()
    Dim helpInputLst As Variant
    pasteCol = 1
    
    With ThisWorkbook.Worksheets(stHelpInput)
        lastRow = .Cells(Rows.count, 1).End(xlUp).row
        If lastRow < 4 Then lastRow = 4
        lastCol = .Cells(3, 1).End(xlToRight).Column
        helpInputLst = .Range(.Cells(4, 1), .Cells(lastRow, lastCol))
    End With
    
    For i = LBound(helpInputLst) To UBound(helpInputLst)
        For j = LBound(helpInputLst, 2) To UBound(helpInputLst, 2)
            target = helpInputLst(i, startConCol + 2 * (j - 1) + conTargetCol)
            If target = "" Then Exit For
            pkgNum = helpInputLst(i, startConCol + 2 * (j - 1) + conNameCol)
            targetPkg = target & "^" & pkgNum
            
            ThisWorkbook.Worksheets(stReadPkg).Cells(mainLabelRow, pasteCol + 1) = targetPkg
            pasteCol = pasteCol + 1
        Next j
    Next i
    
    ThisWorkbook.Worksheets(stReadPkg).Select
    Call GatherData
End Sub

Sub PlacePkgData()
    Call initialize
    
    With ThisWorkbook.Worksheets(stReadPkg)
    
    lastRow = .Cells(Rows.count, 1).End(xlUp).row
    lastCol = .Cells(mainLabelRow, 1).End(xlToRight).Column
    
    resultFileHead = .Cells(1, 2)
    pkgRootDir = .Cells(2, 2)
    
    resultLabel = .Range(.Cells(mainLabelRow, 1), .Cells(mainLabelRow, lastCol))
    resultLst = .Range(.Cells(mainStartRow, 1), .Cells(lastRow, lastCol))
    
    End With
    
    For j = 2 To UBound(resultLabel, 2)
        DoEvents
        Application.StatusBar = j & "/" & UBound(resultLabel, 2)
        
        routeId = resultLabel(1, j)
        splitRouteId = Split(routeId, "^")
        target = splitRouteId(0)
        routeNum = splitRouteId(1)
        outDir = Replace(GetDataFolder("PKG", target, routeNum), "<ROOT>", pkgRootDir)
                        
        For i = LBound(resultLst) To UBound(resultLst)
            targetDateTime = resultLst(i, 1)
            targetDate = Format(targetDateTime, "yymmdd")
            Dim outPath As String: outPath = outDir & "\" & resultFileHead & targetDate & ".csv"
            
            If targetDate <> preTargetDate Then
                Call OutputSingleText("Time,Code,Name", outPath)
            End If
            Call AppendSingleText(targetDateTime & "," & resultLst(i, j) & ",Signal", outPath)
            preTargetDate = targetDate
        Next
    Next
    
    MsgBox "出力しました", vbInformation
End Sub

