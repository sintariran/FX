Attribute VB_Name = "パターン表"
Public Const stMain = "メイン"
Public Const stPeriod = "時間足指定値"
Const rangeOutDir = "B1"
Const rangeLogDir = "B2"

Public Const patternTypeCol = 2
Public Const patternObjectCol = 3
Public Const patternOnOffCol = 4
Public Const patternUpdateCol = 5
Public Const patternRouteIdCol = 6
Public Const patternPeriodCol = 7
Public Const patternTermCol = 8
Public Const patternPairCol = 9
Public Const patternLayerCol = 10
Public Const patternTriggerCol = 11
Public Const patternPkgOutCol = 12
Public Const patternRouteOutCol = 13
Public Const patternAndOrCol = 14
Public Const patternConditionStartCol = 15

Public Const patternHeaderRow = 5

Dim patternPath As String
Dim patternLogPath As String
Dim patternHeader As Variant
Dim patternLst As Variant
Dim newPatternLst As Variant
Dim periodValLst As Variant

Sub OutputPatternSetting()
    Call OnOffOptimize
    Call Main
    
    MsgBox "Finish", vbInformation
End Sub

Sub Main()
    Call Initialize
    Call ConvertSystemInput
    
    'MsgBox "Finish", vbInformation
End Sub

Function Initialize()
    newPatternLst = ""
    
    With ThisWorkbook.Worksheets(stMain)
    
    lastRow = .Cells(Rows.Count, 1).End(xlUp).row
    lastCol = .Range("A1").SpecialCells(xlLastCell).Column
    
    patternHeader = .Range(.Cells(patternHeaderRow, 1), .Cells(patternHeaderRow, lastCol))
    patternLst = .Range(.Cells(patternHeaderRow + 1, 1), .Cells(lastRow, lastCol))
    
    dateTimeStr = Format(Now(), "yyyymmddhhnn")
    patternPath = .Range(rangeOutDir) & "\pattern_setting.csv"
    patternLogPath = .Range(rangeLogDir) & "\pattern_setting_" & dateTimeStr & ".csv"
    
    transPatternHeader = Transpose2DLst(patternHeader)
    transPatternHeader1D = ConvertDimension2Dto1D(transPatternHeader)
    Call AddManyItemIntoLst(newPatternLst, Join(transPatternHeader1D, ","))
    
    End With
    
    With ThisWorkbook.Worksheets(stPeriod)
    
    lastRow = .Cells(Rows.Count, 1).End(xlUp).row
    lastCol = .Range("A1").SpecialCells(xlLastCell).Column
    
    periodValLst = .Range(.Cells(3, 1), .Cells(lastRow, lastCol))
        
    End With
End Function

'メイン部分
Function ConvertSystemInput()
    For patternRow = LBound(patternLst) To UBound(patternLst)
        periodStr = patternLst(patternRow, patternPeriodCol)
        termStr = patternLst(patternRow, patternTermCol)
        pairStr = patternLst(patternRow, patternPairCol)
        
        periodLst = Split(periodStr, "/")
        termLst = Split(termStr, "/")
        pairLst = Split(pairStr, "/")
        
        For i = LBound(periodLst) To UBound(periodLst)
            For j = LBound(termLst) To UBound(termLst)
                For k = LBound(pairLst) To UBound(pairLst)
                    periodNum = periodLst(i)
                    termNum = termLst(j)
                    pairNum = pairLst(k)
                    
                    If periodNum <> 0 Then
                        'ターゲットを変換
                        patternRowStr = GetPatternRowStr(patternRow, periodNum, termNum, pairNum)
                        
                        '変換後を新リストに追加する
                        Call AddManyItemIntoLst(newPatternLst, patternRowStr)
                    End If
                Next
            Next
        Next
    Next
    Call EliminateBlankRowFromLst(newPatternLst)
    
    Call RemoveDuplicate(newPatternLst)
    
    Call OutputText1D(newPatternLst, patternPath)
    Call OutputText1D(newPatternLst, patternLogPath)
End Function

'ターゲットを変換してパターン表の行のリストを返す
Function GetPatternRowStr(patternRow, periodNum, termNum, pairNum)
        patternMaxCol = UBound(patternLst, 2)
        For patternCol = patternConditionStartCol To UBound(patternLst, 2)
            If patternLst(patternRow, patternCol) = "" Then
                patternMaxCol = patternCol - 1
                Exit For
            End If
        Next
        routeId = patternLst(patternRow, patternRouteIdCol)
        routeType = patternLst(patternRow, patternTypeCol)
        
        Dim patternRowLst
        ReDim patternRowLst(1 To patternMaxCol)
        patternRowLst(patternTypeCol) = patternLst(patternRow, patternTypeCol)
        patternRowLst(patternObjectCol) = patternLst(patternRow, patternObjectCol)
        patternRowLst(patternOnOffCol) = patternLst(patternRow, patternOnOffCol)
        patternRowLst(patternUpdateCol) = patternLst(patternRow, patternUpdateCol)
        patternRowLst(patternRouteIdCol) = ConvertTarget(routeId, periodNum, termNum, pairNum)
        patternRowLst(patternPeriodCol) = periodNum
        patternRowLst(patternTermCol) = termNum
        patternRowLst(patternPairCol) = pairNum
        patternRowLst(patternLayerCol) = patternLst(patternRow, patternLayerCol)
        patternRowLst(patternTriggerCol) = patternLst(patternRow, patternTriggerCol)
        patternRowLst(patternPkgOutCol) = patternLst(patternRow, patternPkgOutCol)
        patternRowLst(patternRouteOutCol) = patternLst(patternRow, patternRouteOutCol)
        patternRowLst(patternAndOrCol) = patternLst(patternRow, patternAndOrCol)
        
        If routeType = "Z" Or routeType = "B" Or routeType = "AS" Then
            If Not patternRowLst(patternPkgOutCol) Like "#" Then
                ThisWorkbook.ActiveSheet.Cells(patternRow + patternHeaderRow, patternPkgOutCol).Select
                MsgBox "PKG出力値が入力されていません", vbCritical
                End
            End If
        End If
        
        If routeType = "W" Then
            patternRowLst(patternTypeCol) = "S"
            conRouteId = patternLst(patternRow, patternConditionStartCol + termNum)
            patternRowLst(patternConditionStartCol) = ConvertTarget(conRouteId, periodNum, 9, pairNum)
        Else
            For patternCol = patternConditionStartCol To patternMaxCol
                conRouteId = patternLst(patternRow, patternCol)
                If Mid(conRouteId, 5, 2) = "PE" Then
                    For i = LBound(periodValLst) To UBound(periodValLst)
                        If conRouteId = periodValLst(i, 1) Then
                            conRouteId = periodValLst(i, 1 + periodNum)
                        End If
                    Next
                End If
                patternRowLst(patternCol) = ConvertTarget(conRouteId, periodNum, termNum, pairNum)
            Next
        End If

        GetPatternRowStr = Join(patternRowLst, ",")
End Function

Function ConvertTarget(routeId, periodNum, termNum, pairNum)
    splitRouteId = Split(routeId, "^")
    target = splitRouteId(0)
    checkTarget = target
    
    If Left(checkTarget, 1) = "$" Then
        '時間足が固定の場合
        originalPeriod = Mid(checkTarget, 2, 1)
        convertPeriod = originalPeriod
        checkTarget = Right(checkTarget, Len(checkTarget) - 2)
    Else
        originalPeriod = Mid(checkTarget, 1, 1)
        convertPeriod = CInt(originalPeriod) + CInt(periodNum) - 1
        checkTarget = Right(checkTarget, Len(checkTarget) - 1)
    End If
    
    If convertPeriod < 1 Then convertPeriod = 1
    
    If Left(checkTarget, 1) = "$" Then
        originalTerm = Mid(checkTarget, 2, 1)
        convertTerm = originalTerm
        checkTarget = Right(checkTarget, Len(checkTarget) - 2)
    Else
        originalTerm = Mid(checkTarget, 1, 1)
        If originalTerm = "9" Then
            convertTerm = termNum
        Else
            convertTerm = originalTerm
        End If
        checkTarget = Right(checkTarget, Len(checkTarget) - 1)
    End If
    
    If Left(checkTarget, 1) = "$" Then
        originalPair = Mid(checkTarget, 2, 1)
        convertPair = originalPair
    Else
        originalPair = Mid(checkTarget, 1, 1)
        If originalPair = "1" Then
            convertPair = pairNum
        Else
            convertPair = originalPair
        End If
    End If
    
    ConvertTarget = convertPeriod & convertTerm & convertPair & "^" & splitRouteId(1)
End Function
