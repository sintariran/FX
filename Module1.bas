Attribute VB_Name = "Module1"
Const mainSt = "�W�v"
Const branchLogSt = "branch_log"
Const tradeSettingSt = "trade_setting"
Const historySt = "trade_history"

Const branchTimeCol = 1
Const branchStrCol = 2
Const branchDirectionCol = 3
Const branchIdealCol = 4
Const branchMatchCol = 5

Const hisWinLoseCol = 1
Const hisBuySellCol = 2
Const hisLotCol = 3
Const hisPairCol = 4
Const hisEntryTimeCol = 5
Const hisEntryPriceCol = 6
Const hisExitTimeCol = 7
Const hisExitPriceCol = 8
Const hisProfitPipsCol = 9
Const hisProfitYenCol = 10
Const hisMaxProfitCol = 11
Const hisMaxDDCol = 12
Const hisBranchLogCol = 13

Const aggreRowCol = 1
Const aggreMatchCol = 2
Const aggreUnMatchCol = 3
Const aggreMatchRatioCol = 4
Const aggreOrderCol = 5
Const aggreWinCountCol = 6
Const aggreLoseCountCol = 7
Const aggreWinRatioCol = 8
Const aggreProfitCol = 9
Const aggreAveProfitCol = 10
Const aggreAveMaxProfitCol = 11
Const aggreAveMaxDdCol = 12
Const aggreNameStartCol = 13

Const pasteResultRow = 8

Dim tradeLst As Variant
Dim branchLst As Variant
Dim historyLst As Variant
Dim aggreLst As Variant

Sub AggregateResult()
    Call Initialize
    
    'BranchLog���W�v���ʂɕ��z
    For branchRow = LBound(branchLst) + 1 To UBound(branchLst)
        If branchRow Mod 1000 = 0 Then
            DoEvents
            Application.StatusBar = "���C��������... " & branchRow & "/" & UBound(branchLst)
        End If
        branchStr = branchLst(branchRow, branchStrCol)
        If branchStr <> "" Then
            branchStrLst = Split(branchStr, ">")
            For i = LBound(branchStrLst) To UBound(branchStrLst)
                If IsNumeric(branchStrLst(i)) Then
                    tradeRow = CInt(branchStrLst(i)) + 1
                    If branchLst(branchRow, branchMatchCol) = True Then
                        aggreLst(tradeRow, aggreMatchCol) = aggreLst(tradeRow, aggreMatchCol) + 1
                    Else
                        aggreLst(tradeRow, aggreUnMatchCol) = aggreLst(tradeRow, aggreUnMatchCol) + 1
                    End If
                End If
            Next
        End If
    Next
    
    'trade_history���W�v���ʂɕ��z
    For hisRow = LBound(historyLst) + 1 To UBound(historyLst)
        If hisRow Mod 100 = 2 Then
            DoEvents
            Application.StatusBar = "���C������2��... " & hisRow & "/" & UBound(historyLst)
        End If
    
        winLose = historyLst(hisRow, hisWinLoseCol)
        profit = CDbl(historyLst(hisRow, hisProfitPipsCol))
        maxProfit = CDbl(historyLst(hisRow, hisMaxProfitCol))
        maxDd = CDbl(historyLst(hisRow, hisMaxDDCol))
        branchLog = historyLst(hisRow, hisBranchLogCol)
        If branchLog <> "" Then
            branchStrLst = Split(branchLog, ">")
            For i = LBound(branchStrLst) To UBound(branchStrLst)
                If IsNumeric(branchStrLst(i)) Then
                    tradeRow = CInt(branchStrLst(i)) + 1
                    If winLose = "WIN" Then
                        aggreLst(tradeRow, aggreWinCountCol) = aggreLst(tradeRow, aggreWinCountCol) + 1
                    Else
                        aggreLst(tradeRow, aggreLoseCountCol) = aggreLst(tradeRow, aggreLoseCountCol) + 1
                    End If
                    aggreLst(tradeRow, aggreProfitCol) = aggreLst(tradeRow, aggreProfitCol) + profit
                    aggreLst(tradeRow, aggreAveMaxProfitCol) = aggreLst(tradeRow, aggreAveMaxProfitCol) + maxProfit
                    aggreLst(tradeRow, aggreAveMaxDdCol) = aggreLst(tradeRow, aggreAveMaxDdCol) + maxDd
                End If
            Next
        End If
    Next
    
    For aggreRow = LBound(aggreLst) To UBound(aggreLst)
        matchNum = aggreLst(aggreRow, aggreMatchCol)
        If matchNum = "" Then aggreLst(aggreRow, aggreMatchCol) = 0
        unMatchNum = aggreLst(aggreRow, aggreUnMatchCol)
        If unMatchNum = "" Then aggreLst(aggreRow, aggreUnMatchCol) = 0
        
        If matchNum <> 0 Then
            aggreLst(aggreRow, aggreMatchRatioCol) = matchNum / (matchNum + unMatchNum)
        Else
            aggreLst(aggreRow, aggreMatchRatioCol) = 0
        End If
        
        winCount = aggreLst(aggreRow, aggreWinCountCol)
        loseCount = aggreLst(aggreRow, aggreLoseCountCol)
        If winCount <> "" Or loseCount <> "" Then
            aggreLst(aggreRow, aggreWinRatioCol) = winCount / (winCount + loseCount)
            aggreLst(aggreRow, aggreAveProfitCol) = aggreLst(aggreRow, aggreProfitCol) / (winCount + loseCount)
            aggreLst(aggreRow, aggreAveMaxProfitCol) = aggreLst(aggreRow, aggreAveMaxProfitCol) / (winCount + loseCount)
            aggreLst(aggreRow, aggreAveMaxDdCol) = aggreLst(aggreRow, aggreAveMaxDdCol) / (winCount + loseCount)
        End If
    Next
    
    Call PasteResult
    MsgBox "Finish", vbInformation
End Sub

Function Initialize()
    With ThisWorkbook.ActiveSheet
    tradeDir = .Range("B1").Value
    branchDir = .Range("B2").Value
    historyDir = .Range("B3").Value
    targetFileName = Split(.Range("B4").Value, "/")
    heikinRouteId = .Range("B5").Value
    
    splitFileName = Split(targetFileName(0), "_")
    targetDate = splitFileName(3)
    tradePath = GetFilePath(tradeDir, "trade_setting", targetDate)
    If tradePath = "" Then
        MsgBox "trade_setting���݂���܂���", vbCritical
        End
    End If
    tradeLst = ReadCsv(tradePath)
    tradeLst = ConvertDimensionToSplitComma(tradeLst)
    
    '�W�v���ʃ��X�g�̍쐬
    ReDim aggreLst(1 To UBound(tradeLst), 1 To aggreNameStartCol + UBound(tradeLst, 2))
    For aggreRow = LBound(aggreLst) To UBound(aggreLst)
        For tradeCol = 1 To UBound(tradeLst, 2)
            tradeStr = Trim(tradeLst(aggreRow, tradeCol))
            If tradeStr <> "" Then
                aggreLst(aggreRow, aggreRowCol) = aggreRow
                aggreLst(aggreRow, aggreNameStartCol + tradeCol) = tradeStr
                Exit For
            End If
        Next
    Next
    
    For i = LBound(targetFileName) To UBound(targetFileName)
        splitFileName = Split(targetFileName(i), "_")
        targetDate = splitFileName(2) & "_" & splitFileName(3)
        branchPath = GetFilePath(branchDir, "branch_log", targetDate)
        If branchPath = "" Then
            MsgBox "branch_log���݂���܂���", vbCritical
            End
        End If
        readBranchLst = ReadCsv(branchPath)
        If i <> LBound(targetFileName) Then
            Call RemoveHeaderFromLst(readBranchLst, 1)
            branchLst = CombineList(branchLst, readBranchLst)
        Else
            branchLst = readBranchLst
        End If
    Next
    branchLst = ConvertDimensionToSplitComma(branchLst)
        
    '�������f����
    ReDim Preserve branchLst(1 To UBound(branchLst), 1 To 5)
    branchLst(1, branchDirectionCol) = "�������f"
    For branchRow = LBound(branchLst) + 1 To UBound(branchLst)
        branchStr = branchLst(branchRow, branchStrCol)
        If branchStr <> "" Then
            If Right(branchStr, 5) = "�G���g���[" Then
                If Right(branchStr, 6) = "��G���g���[" Then
                    branchLst(branchRow, branchDirectionCol) = 1
                Else
                    branchLst(branchRow, branchDirectionCol) = 2
                End If
            ElseIf Right(branchStr, 4) = "�T������" Then
                branchLst(branchRow, branchDirectionCol) = ""
            Else
                branchLst(branchRow, branchDirectionCol) = branchLst(branchRow - 1, branchDirectionCol)
            End If
        End If
    Next
    
    Dim targetBranchRow As Long: targetBranchRow = 2
    For j = LBound(targetFileName) To UBound(targetFileName)
        splitFileName = Split(targetFileName(j), "_")
        targetDate = splitFileName(2) & "_" & splitFileName(3)
        pkgPath = GetFilePath(branchDir, "pkg_log", targetDate)
        If pkgPath = "" Then
            MsgBox "pkg_log���݂���܂���", vbCritical
            End
        End If
        Application.StatusBar = "�t�@�C���ǂݍ��ݒ�" & j & "/" & UBound(targetFileName)
        pkgLst = ReadCsv(pkgPath)
        routeIdLst = Split(pkgLst(0), ",")
        For i = LBound(routeIdLst) + 1 To UBound(routeIdLst)
            targetRouteId = routeIdLst(i)
            If targetRouteId = heikinRouteId Then
                targetCol = i
                Exit For
            End If
        Next
        If targetCol = "" Then
            MsgBox "���ϑ�" & heikinRouteId & "���݂���܂���", vbCritical
            End
        End If
        For pkgRow = LBound(pkgLst) + 1 To UBound(pkgLst)
            If pkgRow Mod 1000 = 0 Then
                DoEvents
                Application.StatusBar = "�����ݒ蒆" & pkgRow & "/" & UBound(pkgLst)
            End If
            pkgRowLst = Split(pkgLst(pkgRow), ",")
            branchLst(targetBranchRow, branchIdealCol) = pkgRowLst(targetCol)
            targetBranchRow = targetBranchRow + 1
        Next
    Next
        
    Dim ashiNumLst(1 To 9)
    ashiNumLst(1) = 1
    ashiNumLst(2) = 5
    ashiNumLst(3) = 15
    ashiNumLst(4) = 30
    ashiNumLst(5) = 60
    ashiNumLst(6) = 240
    ashiNumLst(7) = 1440
    periodNum = Left(heikinRouteId, 1)
    ashiNum = ashiNumLst(periodNum)
    
    Set branchDic = CreateObject("Scripting.Dictionary")
    For i = LBound(branchLst) + 1 To UBound(branchLst) - ashiNum
        branchLst(i, branchIdealCol) = branchLst(i + ashiNum, branchIdealCol)
        If branchLst(i, branchDirectionCol) = CInt(branchLst(i, branchIdealCol)) Then
            branchLst(i, branchMatchCol) = True
        Else
            branchLst(i, branchMatchCol) = False
        End If
        
        branchTime = branchLst(i, branchTimeCol)
        branchStr = branchLst(i, branchStrCol)
        If Not branchDic.exists(branchTime) Then
            branchDic.Add branchTime, branchStr
        End If
    Next
    
    'trade_history�̓ǂݍ���
    For i = LBound(targetFileName) To UBound(targetFileName)
        splitFileName = Split(targetFileName(i), "_")
        targetDate = splitFileName(2) & "_" & splitFileName(3)
        tradeHisPath = GetFilePath(historyDir, "trade_history", targetDate)
        If tradeHisPath = "" Then
            MsgBox "trade_history���݂���܂���", vbCritical
            End
        End If
        readHistoryLst = ReadCsv(tradeHisPath)
        If i <> LBound(targetFileName) Then
            Call RemoveHeaderFromLst(readHistoryLst, 1)
            historyLst = CombineList(historyLst, readHistoryLst)
        Else
            historyLst = readHistoryLst
        End If
    Next
    historyLst = ConvertDimensionToSplitComma(historyLst)
    
    ReDim Preserve historyLst(1 To UBound(historyLst), 1 To UBound(historyLst, 2) + 1)
    For i = LBound(historyLst) + 1 To UBound(historyLst)
        entryTime = historyLst(i, hisEntryTimeCol)
        branchLog = branchDic.Item(entryTime)
        historyLst(i, hisBranchLogCol) = branchLog
    Next
    
    End With
End Function

Function GetFilePath(fileDir, fileHeadName, targetDate)
    Set fso = CreateObject("Scripting.FileSystemObject") ' �C���X�^���X��
    Set fl = fso.GetFolder(fileDir) ' �t�H���_���擾
    For Each f In fl.Files ' �t�H���_���̃t�@�C�����擾
        If f.Name Like fileHeadName & "*" Then
            If f.Name Like "*" & targetDate & "*" Then
                GetFilePath = f.Path
                Exit Function
            End If
        End If
    Next
End Function

Function PasteResult()
    With ThisWorkbook.Worksheets(branchLogSt)
    .Cells.Clear
    .Range(.Cells(1, 1), .Cells(UBound(branchLst), UBound(branchLst, 2))) = branchLst
    End With
    
    With ThisWorkbook.Worksheets(tradeSettingSt)
    .Cells.Clear
    .Range(.Cells(1, 1), .Cells(UBound(tradeLst), UBound(tradeLst, 2))) = tradeLst
    End With

    With ThisWorkbook.Worksheets(historySt)
    .Cells.Clear
    .Range(.Cells(1, 1), .Cells(UBound(historyLst), UBound(historyLst, 2))) = historyLst
    End With

    With ThisWorkbook.Worksheets(mainSt)
    .Range(.Cells(pasteResultRow, 1), .Cells(Rows.Count, UBound(aggreLst, 2))).ClearContents
    .Range(.Cells(pasteResultRow, 1), .Cells(UBound(aggreLst), UBound(aggreLst, 2))) = aggreLst
    End With
End Function
