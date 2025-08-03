Attribute VB_Name = "OnOff�œK��"
Const tradeSettingPathRange = "B3"

Dim tradeSettingLst As Variant
Dim patternSettingLst As Variant
Dim pkgNameDic As Variant
Dim groupRowDic As Variant
Dim groupDic As Variant

Sub OnOffOptimize()
    Call InitializeOptimize
    
    '�^�[�Q�b�g�œK��
    Call OptimizeTarget(2, 2, 191)
    
    '�͂���O���[�v��ONOFF
    Call CheckHagureGroup
    
    '�e�q�֌W�œK��
    Call OptimizeParentRelation
    
    '�^�[�Q�b�g���ёւ�
    Call OrderTarget(patternPeriodCol)
    Call OrderTarget(patternTermCol)
    Call OrderTarget(patternPairCol)
    
    '�s�x�X�V�t���O�̊m�F
    Call CheckEveryTimeUpdateFlg
    
    '�\��t��
    Call PasteOnItem
    'MsgBox "trade_setting�ɂ̂��Ƃ�On/Off���œK�����܂���", vbInformation
End Sub

Function InitializeOptimize()
    With ThisWorkbook.Worksheets(stMain)
    tradeSettingPath = .Range(tradeSettingPathRange).Value
    
    lastRow = .Cells(Rows.Count, 1).End(xlUp).row
    lastCol = .Range("A1").SpecialCells(xlLastCell).Column
    patternSettingLst = .Range(.Cells(1, 1), .Cells(lastRow, lastCol))
    
    If .FilterMode = True Then
        .showAllData
    End If
    
    '���[�gID�d���`�F�b�N
    Set duplicateDic = CreateObject("Scripting.Dictionary")
    Set pkgNameDic = CreateObject("Scripting.Dictionary")
    For i = patternHeaderRow + 1 To UBound(patternSettingLst)
        routeId = patternSettingLst(i, patternRouteIdCol)
        If duplicateDic.exists(routeId) Then
            .Cells(i, patternRouteIdCol).Select
            MsgBox "���[�gID�ɏd�����������Ă��܂�" & vbCrLf & routeId, vbCritical
            End
        Else
            duplicateDic.Add routeId, 1
        End If
        
        pkgName = patternSettingLst(i, patternObjectCol)
        If pkgNameDic.exists(pkgName) Then
            .Cells(i, patternObjectCol).Select
            MsgBox "PKG���̂ɏd�����������Ă��܂�" & vbCrLf & pkgName, vbCritical
            End
        Else
            pkgNameDic.Add pkgName, i
        End If
    Next
        
    'On/Off������
    For i = patternHeaderRow + 1 To UBound(patternSettingLst)
        patternSettingLst(i, patternOnOffCol) = 0
        patternSettingLst(i, patternPeriodCol) = ""
        patternSettingLst(i, patternTermCol) = ""
        patternSettingLst(i, patternPairCol) = 1
    Next
    End With
    
    tradeSettingLst = ReadCsv(tradeSettingPath)
    tradeSettingLst = ConvertDimensionToSplitComma(tradeSettingLst)
    Set groupDic = CreateObject("Scripting.Dictionary")
    Set groupRowDic = CreateObject("Scripting.Dictionary")
    For i = LBound(tradeSettingLst) To UBound(tradeSettingLst)
        groupName = tradeSettingLst(i, 1)
        If groupName <> "" And Len(groupName) > 1 Then
            groupRowDic.Add groupName, i
        End If
    Next
End Function

'+------------------------------------------------------------------+
'| �O���[�v���̌���                             |
'+------------------------------------------------------------------+
Function OptimizeTarget(targetRow, targetCol, criteriaTarget)
    If targetCol > UBound(tradeSettingLst, 2) Then
        Exit Function
    End If
    
    Dim isExistValue As Boolean
    For tradeRow = targetRow To UBound(tradeSettingLst)
        DoEvents
        targetVal = tradeSettingLst(tradeRow, targetCol)
        
        '�O���[�v�̍ŏI�s�ɂ�����u���C�N
        If Len(targetVal) = 1 Then Exit For
        
        If targetVal <> "" Then
            isExistValue = True
            If Left(targetVal, 1) = ">" Then
                groupType = Mid(targetVal, 2, 1)
                If groupType = "E" Or groupType = "T" Then
                    target = Mid(targetVal, 3, 3)
                    groupName = Right(targetVal, Len(targetVal) - 5)
                    nextRow = groupRowDic.Item(groupName)
                    convTarget = ConvertTarget(target, criteriaTarget)
                    If Left(target, 1) = "0" And Left(criteriaTarget, 1) = "1" Then
                        convTarget = "0" & Right(convTarget, 2)
                    End If
                                   
                    If Not groupDic.exists(convTarget & groupName) Then
                        Call OptimizeTarget(nextRow + 1, 2, convTarget)
                    End If
                Else
                    target = Mid(targetVal, 2, 3)
                    convTarget = ConvertTarget(target, criteriaTarget)
                    If Left(target, 1) = "0" And Left(criteriaTarget, 1) = "1" Then
                        convTarget = "0" & Right(convTarget, 2)
                    End If
                    groupName = Right(targetVal, Len(targetVal) - 4)
                    nextRow = groupRowDic.Item(groupName)
                    
                    If Not groupDic.exists(convTarget & groupName) Then
                        Call OptimizeTarget(nextRow + 1, 2, convTarget)
                        groupDic.Add convTarget & groupName, 1
                    End If
                End If
            Else
                target = Left(targetVal, 3)
                If IsNumeric(target) Then
                    pkgName = Right(targetVal, Len(targetVal) - 3)
                    Call AddTarget(criteriaTarget, target, pkgName)
                    patternRow = pkgNameDic.Item(pkgName)
                    patternSettingLst(patternRow, patternOnOffCol) = 1
                End If
            End If
        End If
    Next

    '����ɒl�����݂��Ă���Ύ��̗����������
    If isExistValue Then
        Call OptimizeTarget(targetRow, targetCol + 1, criteriaTarget)
    End If
End Function

Function CheckHagureGroup()
    For tradeRow = 1 To UBound(tradeSettingLst)
        For tradeCol = 1 To UBound(tradeSettingLst, 2)
            DoEvents
            targetVal = tradeSettingLst(tradeRow, tradeCol)
            
            '�O���[�v�̍ŏI�s�ɂ�����u���C�N
            If Len(targetVal) = 1 Then Exit For
            
            If targetVal <> "" Then
                isExistValue = True
                If Not Left(targetVal, 1) = ">" Then
                    target = Left(targetVal, 3)
                    If IsNumeric(target) Then
                        pkgName = Right(targetVal, Len(targetVal) - 3)
                        patternRow = pkgNameDic.Item(pkgName)
                        If patternSettingLst(patternRow, patternOnOffCol) = 0 Then
                            Call AddTarget(191, target, pkgName)
                            patternSettingLst(patternRow, patternOnOffCol) = 1
                        End If
                    End If
                End If
            End If
        Next
    Next
End Function

'�^�[�Q�b�g�̕ϊ�
Function ConvertTarget(target, criteriaTarget)
    returnTarget = target

    '���ԑ��̕ϊ�
    targetPeriod = CInt(Left(target, 1)) + CInt(Left(criteriaTarget, 1)) - 1
   
    If targetPeriod < 1 Then
        targetPeriod = 1
    ElseIf targetPeriod > 9 Then
        targetPeriod = 9
    End If
    returnTarget = targetPeriod & Right(target, 2)
    
    If Not Mid(criteriaTarget, 2, 1) = "9" Then
      returnTarget = Left(target, 1) + Mid(criteriaTarget, 2, 1) + Right(target, 1)
    End If

    If Right(criteriaTarget, 1) <> "1" Then
        '�ʉ݂̕ϊ��ɂ��ċL��
    End If
    
    ConvertTarget = returnTarget
End Function

'pattern_setting�Ƀ^�[�Q�b�g��ǉ�����
Function AddTarget(criteriaTarget, target, pkgName)
    If pkgNameDic.exists(pkgName) Then
        patternRow = pkgNameDic.Item(pkgName)
    Else
        MsgBox pkgName & "�͑��݂��܂���", vbCritical
        End
    End If
    
    criteriaPeriod = Mid(criteriaTarget, 1, 1)
    criteriaTerm = Mid(criteriaTarget, 2, 1)
    criteriaPair = Mid(criteriaTarget, 3, 1)
    
    targetPeriod = CInt(Mid(target, 1, 1)) + CInt(criteriaPeriod) - 1
    targetTerm = Mid(target, 2, 1)
    If targetTerm = "9" Then
        targetTerm = criteriaTerm
    End If
    targetPair = Mid(target, 3, 1)
    If targetPair = "1" Then
        '�ʉ݂̕ϊ����@�ɂ��ċL��
    End If
    
    If targetPeriod > 0 And targetPeriod < 10 Then
        Call AddTargetItem(patternRow, patternPeriodCol, targetPeriod)
    End If
    Call AddTargetItem(patternRow, patternTermCol, targetTerm)
    Call AddTargetItem(patternRow, patternPairCol, targetPair)
End Function

Function AddTargetItem(patternRow, targetCol, targetItem)
    nowItem = patternSettingLst(patternRow, targetCol)
    If Not nowItem Like "*" & targetItem & "*" Then
        If nowItem = "" Then
            patternSettingLst(patternRow, targetCol) = targetItem
        Else
            patternSettingLst(patternRow, targetCol) = nowItem & "/" & targetItem
        End If
    End If
End Function

Function OptimizeParentRelation()
    For patternRow = UBound(patternSettingLst) To patternHeaderRow Step -1
        onoff = patternSettingLst(patternRow, patternOnOffCol)
        If onoff = 1 Then
            routeId = patternSettingLst(patternRow, patternRouteIdCol)
            Call OptimizeParent(routeId, patternRow)
        End If
    Next
End Function

Function OptimizeParent(routeId, childRow)
    Dim needOptParent As Boolean: needOptParent = True
    splitRouteId = Split(routeId, "^")
    target = splitRouteId(0)
    regId = splitRouteId(1)
    For parentRow = childRow To patternHeaderRow Step -1
        targetId = patternSettingLst(parentRow, patternRouteIdCol)
        If targetId Like "*" & regId Then
            If parentRow <> childRow Then
                '���ԑ��A���ԁA�ʉ݂����낦��
                pkgName = patternSettingLst(parentRow, patternObjectCol)
                needOptParent = AddTargetGroup(target, childRow, parentRow)
            End If
            
            '�X�C�b�`��ON�ɂ���
            If patternSettingLst(parentRow, patternOnOffCol) = 0 Then
                patternSettingLst(parentRow, patternOnOffCol) = 1
            End If
            
            '��ʊK�w��T������
            If needOptParent Then
                For j = patternConditionStartCol To UBound(patternSettingLst, 2)
                    conName = patternSettingLst(parentRow, j)
                    If conName Like "*191^1-8" Then
                    Debug.Print
                    End If
                    If conName <> "" Then
                        test1 = patternSettingLst(childRow, patternPairCol)
                        test2 = patternSettingLst(parentRow, patternPairCol)
                        Call OptimizeParent(conName, parentRow)
                    Else
                        Exit For
                    End If
                Next
            End If
            Exit For
        End If
    Next
End Function

Function AddTargetGroup(criteriaTarget, childRow, parentRow)
    Dim isFixPeriod As Boolean, isFixTerm As Boolean, isFixPair As Boolean
    
    If InStr(criteriaTarget, "$") > 0 Then
        tmp = criteriaTarget
        If Left(tmp, 1) = "$" Then
            isFixPeriod = True
            tmp = Right(tmp, Len(tmp) - 2)
        Else
            tmp = Right(tmp, Len(tmp) - 1)
        End If
        
        If Left(tmp, 1) = "$" Then
            isFixTerm = True
            tmp = Right(tmp, Len(tmp) - 2)
        Else
            tmp = Right(tmp, Len(tmp) - 1)
        End If
        
        If Left(tmp, 1) = "$" Then
            isFixPair = True
            tmp = Right(tmp, Len(tmp) - 2)
        Else
            tmp = Right(tmp, Len(tmp) - 1)
        End If
        criteriaTarget = Replace(criteriaTarget, "$", "")
    End If
    
    '���ԑ�
    isUpdatePeriod = AddTargetItemGroup(Mid(criteriaTarget, 1, 1), childRow, parentRow, patternPeriodCol, isFixPeriod)
    
    '����
    If patternSettingLst(parentRow, patternTypeCol) = "W" Then
        conditionNum = 0
        For i = patternConditionStartCol To UBound(patternSettingLst, 2)
            If patternSettingLst(parentRow, i) = "" Then Exit For
            If termStr = "" Then
                termStr = conditionNum
            Else
                termStr = termStr & "/" & conditionNum
            End If
            conditionNum = conditionNum + 1
        Next
        patternSettingLst(parentRow, patternTermCol) = termStr
    ElseIf patternSettingLst(childRow, patternTypeCol) = "W" Then
        patternSettingLst(parentRow, patternTermCol) = "9"
    Else
        isUpdateTerm = AddTargetItemGroup(Mid(criteriaTarget, 2, 1), childRow, parentRow, patternTermCol, isFixTerm)
    End If
    
    '�ʉ�
    isUpdatePair = AddTargetItemGroup(Mid(criteriaTarget, 3, 1), childRow, parentRow, patternPairCol, isFixPair)
    
    If isUpdatePeriod Or isUpdateTerm Or isUpdatePair Then
        AddTargetGroup = True
    Else
        AddTargetGroup = False
    End If
End Function

Function AddTargetItemGroup(criteriaItem, childRow, parentRow, targetCol, isFix)
    Dim isUpdate As Boolean
    childItemLst = Split(patternSettingLst(childRow, targetCol), "/")
    parentItemStr = patternSettingLst(parentRow, targetCol)
    For i = LBound(childItemLst) To UBound(childItemLst)
        If targetCol = patternPeriodCol Then
            '���ԑ�
            If isFix Then
                childItem = criteriaItem
            Else
                childItem = CInt(childItemLst(i)) + CInt(criteriaItem) - 1
            End If
            If childItem < 1 Then childItem = 1
            If childItem > 9 Then childItem = 9
        ElseIf targetCol = patternTermCol Then
            '����
            If childItemLst(i) = "9" Or isFix Then
                childItem = criteriaItem
            Else
                childItem = childItemLst(i)
            End If
        Else
            '�ʉ�
            If criteriaItem = "1" Then
                childItem = childItemLst(i)
            Else
                '�K�v�Ȃ�Βʉݕϊ��̎�������
                childItem = criteriaItem
            End If
        End If
        
        If Not parentItemStr Like "*" & childItem & "*" Then
            If parentItemStr = "" Then
                parentItemStr = childItem
            Else
                parentItemStr = parentItemStr & "/" & childItem
            End If
            isUpdate = True
        End If
    Next
    patternSettingLst(parentRow, targetCol) = parentItemStr
    AddTargetItemGroup = isUpdate
End Function

Function OrderTarget(targetCol)
    For i = LBound(patternSettingLst) To UBound(patternSettingLst)
        targetStr = patternSettingLst(i, targetCol)
        If Len(targetStr) > 1 Then
            targetLst = Split(targetStr, "/")
            Call QuickSort(targetLst)
            patternSettingLst(i, targetCol) = Join(targetLst, "/")
        End If
    Next
End Function

Function CheckEveryTimeUpdateFlg()
    For i = patternHeaderRow + 1 To UBound(patternSettingLst)
        etuFlg = patternSettingLst(i, patternUpdateCol)
        If etuFlg <> 0 Then
            routeId = patternSettingLst(i, patternRouteIdCol)
            routeNum = Right(routeId, Len(routeId) - 3)
            Call CheckChildOfEveryTimeUpdateFlg(routeNum, i + 1)
        End If
    Next
End Function

Function CheckChildOfEveryTimeUpdateFlg(checkRouteNum, checkStartRow)
    For patternRow = checkStartRow To UBound(patternSettingLst)
        For patternCol = patternConditionStartCol To UBound(patternSettingLst, 2)
            conName = patternSettingLst(patternRow, patternCol)
            If conName = "" Then Exit For
            If conName Like "*" & checkRouteNum Then
                etuFlg = patternSettingLst(patternRow, patternUpdateCol)
                If etuFlg = 0 Then
                    If patternRow = 166 Then
                    Debug.Print
                    End If
                    patternSettingLst(patternRow, patternUpdateCol) = 1
                    routeId = patternSettingLst(patternRow, patternRouteIdCol)
                    routeNum = Right(routeId, Len(routeId) - 3)
                    Call CheckChildOfEveryTimeUpdateFlg(routeNum, patternRow + 1)
                End If
                Exit For
            End If
        Next
    Next
End Function

Function PasteOnItem()
    With ThisWorkbook.Worksheets(stMain)
    pasteLst = ExtractColumn(patternSettingLst, patternOnOffCol)
    .Range(.Cells(1, patternOnOffCol), .Cells(UBound(pasteLst), patternOnOffCol)) = pasteLst
    
    pasteLst = ExtractColumn(patternSettingLst, patternUpdateCol)
    .Range(.Cells(1, patternUpdateCol), .Cells(UBound(pasteLst), patternUpdateCol)) = pasteLst
    
    pasteLst = ExtractColumn(patternSettingLst, patternPeriodCol)
    .Range(.Cells(1, patternPeriodCol), .Cells(UBound(pasteLst), patternPeriodCol)) = pasteLst
    
    pasteLst = ExtractColumn(patternSettingLst, patternTermCol)
    .Range(.Cells(1, patternTermCol), .Cells(UBound(pasteLst), patternTermCol)) = pasteLst
    
    pasteLst = ExtractColumn(patternSettingLst, patternPairCol)
    .Range(.Cells(1, patternPairCol), .Cells(UBound(pasteLst), patternPairCol)) = pasteLst
    End With
End Function
