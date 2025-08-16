Attribute VB_Name = "Module1"
Const StNameinput = "Input"
Const StNameoutput = "Output"

Const PasteStartCol1 = 2
Const DateCol = 1

Const maxperiod = 6
Const HeadgePips = 0.01
Const startperiod = 3

Const SituationNumberRow = 1
Const SituationStartRow = 2
Const CategoryRow = 8
Const NameRow = 9
Const StartRow = 10

'入力シート
Const inSituationAssembleColName = "状況コード統合"
Const inSituationNameColName = "状況名単体"
Const inSituationCodeColName = "状況コード単体"
Const inDirectionColName = "方向判断"
Const inFunctionColName = "関数素材"

'出力シート
Const OutLogicNameColName = "ロジック"
Const OutDirectionColName = "方向"

Const SettingCodeNumRange = "B2"

'方向及び状況コード
Const mtx_situationassemblecol = 1
Const mtx_nb_entry_directcol = 2
Const mtx_nb_exit_directcol = 3
Const mtx_na_entry_directcol = 4
Const mtx_na_exit_directcol = 5
Const mtx_headge_entry_directcol = 6
Const mtx_headge_exit_directcol = 7
Const mtx_hhb_entry_directcol = 8
Const mtx_hhb_exit_directcol = 9
Const mtx_hha_entry_directcol = 10
Const mtx_hha_exit_directcol = 11
Const mtx_maxcol = 11

Dim InSituationAssemblecol As Integer
Dim InSituationNamecol As Integer
Dim InSituationCodecol As Integer
Dim InDirectioncol As Integer
Dim inFunctioncol As Integer

Dim OutLogicNamecol As Integer
Dim OutDirectioncol As Integer

Dim SettingCodeNum As Integer

Dim stinput As Worksheet
Dim stoutput As Worksheet

Dim SettingColNum As String

Dim infomtx() As Variant
Dim rowmtx() As Variant
Dim patternmtx() As Variant

Sub GetSituationCodeAssembles()
    Application.ScreenUpdating = False
    Application.Calculation = xlCalculationManual
    
    Call Initialize
    Call CalcSituationCodeAssembles
    
    Application.ScreenUpdating = True
    'Application.Calculation = xlCalculationAutomatic
    Application.StatusBar = False
    MsgBox "Finished!"
End Sub

Function Initialize()
    Set stinput = ThisWorkbook.Worksheets(StNameinput)
    Set stoutput = ThisWorkbook.Worksheets(StNameoutput)
    
    '計算実行
    stinput.Calculate
    stoutput.Calculate
    
    Dim endcol As Integer
    endcol = stinput.Cells(NameRow, Columns.Count).End(xlToLeft).Column
    
    '列番号の探索
    For i = 1 To endcol
        Dim tmpName As String: tmpName = stinput.Cells(CategoryRow, i)
        Call CheckColName(i, tmpName)
        tmpName = stoutput.Cells(CategoryRow, i)
        Call CheckColName(i, tmpName)
    Next i
    
    'スイッチの値の取得
    SettingCodeNum = stoutput.Range(SettingCodeNumRange)
    
    '初期化クリア処理
    'outputシート
    Dim endrow As Long: endrow = Rows.Count
    endcol = stoutput.Cells(NameRow, Columns.Count).End(xlToLeft).Column
    stoutput.Range(Cells(StartRow, OutLogicNamecol), Cells(endrow, endcol)).Clear
    
    ReDim infomtx(mtx_maxcol, 1)
    ReDim rowmtx(SettingCodeNum)
    ReDim patternmtx(SettingCodeNum, CategoryRow)
    
    stinput.Calculate
    stoutput.Calculate

End Function

Function CheckColName(ByVal num As Integer, ByVal name As String)
    Dim i As Integer: i = num
    Dim tmpName As String: tmpName = name

        If tmpName = inSituationAssembleColName Then
            InSituationAssemblecol = i
        ElseIf tmpName = inSituationCodeColName Then
            InSituationCodecol = i
        ElseIf tmpName = inSituationNameColName Then
            InSituationNamecol = i
        ElseIf tmpName = inDirectionColName Then
            InDirectioncol = i
        ElseIf tmpName = inFunctionColName Then
            inFunctioncol = i
        ElseIf tmpName = OutDirectionColName Then
            OutDirectioncol = i
        ElseIf tmpName = OutLogicNameColName Then
            OutLogicNamecol = i
        End If
End Function

'状況コードリストの作成
Function CalcSituationCodeAssembles()
    
    '参照先の列番号の取得
    Call CheckSituationNum
    
    Dim endcol As Integer
    endcol = stinput.Cells(NameRow, Columns.Count).End(xlToLeft).Column
    For logiccol = 1 To endcol - InDirectioncol + 1
        Dim codelist() As Variant
        ReDim codelist(1)
        '単体の状況コードの取得
        '単体の状況コードから組合せパターンの生成
        Call MakeAllPattern2(logiccol, codelist)
        
        'コードの貼付け及び計算実行による出力方向の取得
        Dim directlist() As Variant
        ReDim directlist(1)
        Call SetSituationCodePattern(logiccol, codelist, directlist)
        
        '方向毎のコードの結合文字列の作成と貼付け
        Call MakeCodeAssembls(logiccol, codelist, directlist)
    
        DoEvents
        Application.StatusBar = "計算実行中_(" & logiccol & "/" & (endcol - InDirectioncol + 1) & ")" & _
                                        String(Int(logiccol / (endcol - InDirectioncol + 1) * 10), "■")
    Next logiccol

End Function

'方向毎のコードの結合文字列の作成と出力
Function MakeCodeAssembls( _
    ByVal logiccol As Long, _
    ByVal codelist As Variant, _
    ByVal directlist As Variant _
)
    '方向毎にコードの文字列の結合を行う
    Dim codeassembles1 As String: codeassembles1 = ""
    Dim codeassembles2 As String: codeassembles2 = ""
    
    For loop_row = 1 To UBound(codelist)
        Dim tmpdirect As String: tmpdirect = directlist(loop_row)
        Dim tmpcodeassemble As String: tmpcodeassemble = codelist(loop_row)
        
        If tmpdirect = "1" Then
            If InStr(codeassembles1, tmpcodeassemble) <= 0 Then
                If codeassembles1 = "" Then
                    codeassembles1 = tmpcodeassemble
                Else
                    codeassembles1 = codeassembles1 & "/" & tmpcodeassemble
                End If
            End If
        ElseIf tmpdirect = "2" Then
            If InStr(codeassembles2, tmpcodeassemble) <= 0 Then
                If codeassembles2 = "" Then
                    codeassembles2 = tmpcodeassemble
                Else
                    codeassembles2 = codeassembles2 & "/" & tmpcodeassemble
                End If
            End If
        End If
    Next loop_row
    
    stoutput.Cells(StartRow, OutLogicNamecol + logiccol - 1) = codeassembles1
    stoutput.Cells(StartRow + 1, OutLogicNamecol + logiccol - 1) = codeassembles2

End Function

'状況コードを貼付けて方向判断結果をセル計算させて、値を取得する
Function SetSituationCodePattern( _
    ByVal logiccol As Long, _
    ByVal codelist As Variant, _
    ByRef directlist As Variant _
)
    'コードリストよりコードの貼付け
    Dim pastemtx As Variant
    ReDim pastemtx(UBound(codelist), SettingCodeNum)
    For loop_row = 1 To UBound(codelist)
    For loop_col = 1 To SettingCodeNum
        pastemtx(loop_row - 1, loop_col - 1) = Mid(codelist(loop_row), loop_col, 1)
    Next loop_col
    Next loop_row
'    Dim tmp_row As Long: tmp_row = StartRow + loop_row - 1
'    Dim tmp_col As Long: tmp_col = InSituationCodecol + loop_col - 1
    stinput.Range(stinput.Cells(StartRow, InSituationCodecol), stinput.Cells(StartRow + UBound(codelist) - 1, InSituationCodecol + SettingCodeNum - 1)) = pastemtx
    
    'セルの計算関数のコピー
    stinput.Cells(StartRow, InDirectioncol + logiccol - 1).Copy
    stinput.Range(stinput.Cells(StartRow + 1, InDirectioncol + logiccol - 1), stinput.Cells(StartRow + UBound(codelist), InDirectioncol + logiccol - 1)).PasteSpecial
    'セルの計算処理実行
    stinput.Calculate

    '方向の出力結果の取得
    ReDim directlist(UBound(codelist))
    For loop_row = 1 To UBound(codelist)
        Dim tmp_row As Long: tmp_row = StartRow + loop_row - 1
        directlist(loop_row) = stinput.Cells(tmp_row, InDirectioncol + logiccol - 1)
    Next

End Function

'状況の組み合わせパターンの作成
Function MakeAllPattern2( _
    ByVal logiccol As Long, _
    ByRef codelist As Variant _
)
    Dim loop_col As Integer: loop_col = 1
    
    '各構成要素の状況コードの分岐数（行数）の取得
    For loop_col = 1 To SettingCodeNum
        '使用コード連番に含まれている場合
        If InStr(stinput.Cells(SituationNumberRow, InDirectioncol + logiccol - 1), "|" & loop_col & "|") > 0 Then
            rowmtx(loop_col) = stinput.Cells(SituationStartRow, InSituationCodecol + loop_col - 1).End(xlDown).Row
            For loop_row = SituationStartRow To rowmtx(loop_col)
                patternmtx(loop_col, loop_row) = stinput.Cells(loop_row, InSituationCodecol + loop_col - 1)
            Next loop_row
        '使用コード連番に含まれていない場合（#扱いにする）
        Else
            rowmtx(loop_col) = SituationStartRow
            loop_row = SituationStartRow
            patternmtx(loop_col, loop_row) = "#"
        End If
    Next loop_col
    
    loop_col = 1
    Dim end_row As Integer: end_row = rowmtx(loop_col)
    Dim write_row As Long: write_row = 1
    For loop_row = SituationStartRow To end_row
        Dim basecode As String: basecode = patternmtx(loop_col, loop_row) & String(SettingCodeNum - 1, ",")
        Dim max_counter As Long: max_counter = end_row - 1
        Call MakeAllPatternSub2(loop_col + 1, basecode, max_counter, write_row, codelist)
    Next loop_row
End Function

Function MakeAllPatternSub2( _
    ByVal loop_col As Integer, _
    ByVal basecode As String, _
    ByVal max_counter As Long, _
    ByRef write_row As Long, _
    ByRef codelist As Variant _
)
        Dim end_row As Integer: end_row = rowmtx(loop_col)
        For loop_row = SituationStartRow To end_row
            Dim tmpcode As String: tmpcode = patternmtx(loop_col, loop_row)
            
            '最終列の場合は次の列参照をしないでコードとして登録する
            If loop_col = SettingCodeNum Then
                If UBound(codelist) < max_counter * (end_row - 1) Then
                    ReDim Preserve codelist(max_counter * (end_row - 1))
                ElseIf UBound(codelist) < write_row Then
                    ReDim Preserve codelist(write_row)
                End If
                Mid(basecode, loop_col) = tmpcode
                codelist(write_row) = basecode
                write_row = write_row + 1
            
'                If write_row Mod 100 = 0 Then
'                    DoEvents
'                    Application.StatusBar = "計算実行中_(" & write_row & "/" & max_counter * (end_row - 1) & ")" & _
'                                                    String(Int(write_row / (max_counter * (end_row - 1)) * 10), "■")
'                End If
            '最終列でない場合は自身のコードを追加して、再起処理する
            Else
                Mid(basecode, loop_col) = tmpcode
                Call MakeAllPatternSub2(loop_col + 1, basecode, max_counter * (end_row - 1), write_row, codelist)
            End If
        Next loop_row

End Function

'状況の組み合わせパターンの作成
Function MakeAllPattern()
    Dim loop_col As Integer: loop_col = 1
    
    '各構成要素の状況コードの分岐数（行数）の取得
    For loop_col = 1 To SettingCodeNum
        rowmtx(loop_col) = stinput.Cells(SituationStartRow, InSituationCodecol + loop_col - 1).End(xlDown).Row
'        Dim write_row As long: write_row = 1
        For loop_row = SituationStartRow To rowmtx(loop_col)
            patternmtx(loop_col, loop_row) = stinput.Cells(loop_row, InSituationCodecol + loop_col - 1)
'            write_row = write_row + 1
        Next loop_row
    Next loop_col
    
    loop_col = 1
    Dim end_row As Integer: end_row = rowmtx(loop_col)
    Dim write_row As Long: write_row = 1
    For loop_row = SituationStartRow To end_row
        Dim basecode As String: basecode = patternmtx(loop_col, loop_row) & String(SettingCodeNum - 1, ",")
        Dim max_counter As Long: max_counter = end_row - 1
        Call MakeAllPatternSub(loop_col + 1, basecode, max_counter, write_row)
    Next loop_row
End Function

Function MakeAllPatternSub( _
    ByVal loop_col As Integer, _
    ByVal basecode As String, _
    ByVal max_counter As Long, _
    ByRef write_row As Long _
)
        Dim end_row As Integer: end_row = rowmtx(loop_col)
        For loop_row = SituationStartRow To end_row
            Dim tmpcode As String: tmpcode = patternmtx(loop_col, loop_row)
            
            '最終列の場合は次の列参照をしないでコードとして登録する
            If loop_col = SettingCodeNum Then
                If UBound(infomtx, 2) < max_counter * (end_row - 1) Then
                    ReDim Preserve infomtx(mtx_maxcol, max_counter * (end_row - 1))
                ElseIf UBound(infomtx, 2) < write_row Then
                    ReDim Preserve infomtx(mtx_maxcol, write_row)
                End If
                Mid(basecode, loop_col) = tmpcode
                infomtx(mtx_situationassemblecol, write_row) = basecode
                write_row = write_row + 1
            
                If write_row Mod 100 = 0 Then
                    DoEvents
                    Application.StatusBar = "計算実行中_(" & write_row & "/" & max_counter * (end_row - 1) & ")" & _
                                                    String(Int(write_row / (max_counter * (end_row - 1)) * 10), "■")
                End If
            '最終列でない場合は自身のコードを追加して、再起処理する
            Else
                Mid(basecode, loop_col) = tmpcode
                Call MakeAllPatternSub(loop_col + 1, basecode, max_counter * (end_row - 1), write_row)
            End If
        Next loop_row

End Function

'セルの使用関数から参照先の状況連番を取得
Function CheckSituationNum()
    
    Dim endcol As Integer
    endcol = stinput.Cells(NameRow, Columns.Count).End(xlToLeft).Column
    
    For loop_col = InDirectioncol To endcol
        '状況コード連番の保持用文字列
        Dim checkstr As String: checkstr = "|"
        '関数文字列の取得
        Dim aryRange() As Range
        Dim var As Variant
        aryRange = getFormulaRange(stinput.Range(stinput.Cells(StartRow, loop_col), stinput.Cells(StartRow, loop_col)))
        For Each var In aryRange
            Dim tmpcol As Long: tmpcol = var.Column
            '参照セルが大本の状況単体コードセルの場合、その状況連番を取得する
            If tmpcol >= InSituationNamecol And tmpcol <= InSituationCodecol + SettingCodeNum - 1 Then
                Dim tmpcodenum As Long: tmpcodenum = stinput.Cells(SituationNumberRow, tmpcol)
                If InStr(checkstr, "|" & tmpcodenum & "|") > 0 Then
                Else
                    checkstr = checkstr & tmpcodenum & "|"
                End If
            '参照セルが大本の状況単体コードセルでない場合、更に先の参照セルを確認する
            Else
                Call CheckSituationNumsub(stinput.Range(var.Address), checkstr)
            End If
'            Debug.Print var.Address(External:=True)
        Next
        
        stinput.Cells(SituationNumberRow, loop_col) = checkstr
    Next

End Function

Function CheckSituationNumsub( _
    ByVal tmprange As Range, _
    ByRef checkstr As String _
)

    Dim aryRange() As Range
    Dim var As Variant
    aryRange = getFormulaRange(tmprange)
    For Each var In aryRange
        Dim tmpcol As Long: tmpcol = var.Column
        '参照セルが大本の状況単体コードセルの場合、その状況連番を取得する
        If tmpcol >= InSituationNamecol And tmpcol <= InSituationCodecol + SettingCodeNum - 1 Then
            Dim tmpcodenum As Long: tmpcodenum = stinput.Cells(SituationNumberRow, tmpcol)
            If InStr(checkstr, "|" & tmpcodenum & "|") > 0 Then
            Else
                checkstr = checkstr & tmpcodenum & "|"
            End If
        '参照セルが大本の状況単体コードセルでない場合、更に先の参照セルを確認する
        Else
            Call CheckSituationNumsub(stinput.Range(var.Address), checkstr)
        End If
'            Debug.Print var.Address(External:=True)
    Next

End Function


Function getFormulaRange(ByVal argRange As Range) As Range()
    Dim sFormula As String
    Dim aryRange() As Range
    Dim tRange As Range
    Dim ix As Long
    Dim i As Long
    Dim flgS As Boolean 'シングルクオートが奇数の時True
    Dim flgD As Boolean 'ダブルクオートが奇数の時True
    Dim sSplit() As String
    Dim sTemp As String
  
    '=以降の計算式
    sFormula = Mid(argRange.FormulaLocal, 2)
    '計算式の中の改行や余分な空白を除去
    sFormula = Replace(sFormula, vbCrLf, "")
    sFormula = Replace(sFormula, vbLf, "")
    sFormula = Trim(sFormula)
  
    flgS = False
    flgD = False
    For i = 1 To Len(sFormula)
        'シングル・ダブルのTrue,Falseを反転
        Select Case Mid(sFormula, i, 1)
            Case "'"
                flgS = Not flgS
            Case """"
                'シングルの中ならシート名
                If Not flgS Then
                    flgD = Not flgD
                End If
        End Select
        Select Case Mid(sFormula, i, 1)
            '各種演算子の判定
            Case "+", "-", "*", "/", "^", ">", "<", "=", "(", ")", "&", ",", " "
                Select Case True
                    Case flgS
                        'シングルの中ならシート名
                        sTemp = sTemp & Mid(sFormula, i, 1)
                    Case flgD
                        'ダブルの中なら無視
                    Case Else
                        '各種演算子をvbLfに置換
                        sTemp = sTemp & vbLf
                End Select
            Case Else
                'ダブルの中なら無視、ただしシングルの中はシート名
                If Not flgD Or flgS Then
                    sTemp = sTemp & Mid(sFormula, i, 1)
                End If
        End Select
    Next
  
    On Error Resume Next
    'vbLfで区切って配列化
    sSplit = Split(sTemp, vbLf)
    ix = 0
    For i = 0 To UBound(sSplit)
        If sSplit(i) <> "" Then
            Err.Clear
            'Application.Evaluateメソッドを使ってRangeに変換
            If InStr(sSplit(i), "!") > 0 Then
                Set tRange = Evaluate(Trim(sSplit(i)))
            Else
                'シート名を含まない場合は、元セルのシート名を付加
                Set tRange = Evaluate("'" & argRange.Parent.name & "'!" & Trim(sSplit(i)))
            End If
            'Rangeオブジェクト化が成功すれば配列へ入れる
            If Err.Number = 0 Then
                ReDim Preserve aryRange(ix)
                Set aryRange(ix) = tRange
                ix = ix + 1
            End If
        End If
    Next
    On Error GoTo 0
    getFormulaRange = aryRange
End Function


'金額計算用貼付けデータ作成
Function MakePasteData()
    '貼付け場所の最下行
    Dim endrow As Integer: endrow = stnormal.Cells(Rows.Count, 1).End(xlUp).Row
    
    Dim entryexitrowlist() As Variant
    ReDim entryexitrowrist(1)
    
    '配列から順番に貼付け処理を実行
    For i = 1 To UBound(allpositionmtx, 2)
        '対象の取引種類を調べる
        Dim positiontype As String: positiontype = allpositionmtx(apmtx_positiontypestcol, i)
        Dim positiondirect As Integer: positiondirect = allpositionmtx(apmtx_directioncol, i)
        
        'エントリー行は金額計算時に決済行と同行だと持ち替え処理が正常に実行されないため、エントリー行を1行繰り下げる
        Dim entryrow As Integer: entryrow = allpositionmtx(apmtx_entryrowcol, i) + 1
        
        '金額計算用関数が最終行は空にしないと正常に値計算されないため、最終行は入力しないために繰り上げする
        Dim exitrow As Integer: exitrow = allpositionmtx(apmtx_exitrowcol, i)
        If exitrow = endrow Then
            exitrow = exitrow - 1
        End If
        
        
        
        
        If positiontype = HAddPositionTypeName Then
            Call MakePasteDataSub(stadd, positiondirect, entryrow, exitrow, positiontype)
        ElseIf positiontype = SAddPositionTypeName Then
            Call MakePasteDataSub(stadd, positiondirect, entryrow, exitrow, positiontype)
        ElseIf positiontype = HeadgePositionTypeName Then
            Call MakePasteDataSub(stheadge, positiondirect, entryrow, exitrow, positiontype)
        ElseIf positiontype = FirstPositionTypeName Then
            Call MakePasteDataSub(stadd, positiondirect, entryrow, exitrow, positiontype)
        End If
        
    Next i

End Function

Function MakePasteDataSub( _
    ByVal tmpst As Worksheet, _
    ByVal positiondirect As Integer, _
    ByVal entryrow As Integer, _
    ByVal exitrow As Integer, _
    ByVal posiname As String _
)
    '貼り付ける値の特定
    Dim pastenum As Integer: pastenum = 0
    If positiondirect = 1 Then
        pastenum = 1
    ElseIf positiondirect = 2 Then
        pastenum = -1
    End If
        
    '開始行の中で空白のセルの列を探して貼付け処理をする
    For tmpcol = PasteStartCol1 To tmpst.Columns.Count
        If tmpst.Cells(entryrow, tmpcol) = Empty Then
            '貼付け列のカラム名にカラム番号を記載する
            tmpst.Cells(NameRow, tmpcol) = posiname & "_" & tmpcol
            'エントリー行から決済行までのループ
            For tmprow = entryrow To exitrow
                tmpst.Cells(tmprow, tmpcol) = pastenum
            Next tmprow
            
            '貼付け完了後ループを抜ける
            Exit For
        End If
    Next tmpcol

End Function


