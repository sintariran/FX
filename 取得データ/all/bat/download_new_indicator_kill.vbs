Call TaskKill

' -----------------------------------------------------
' �Ώۂ�VBS���N�����ꂢ�Ă��邩�m�F���A���m
' �����ꍇ�Ataskkill����B
' -----------------------------------------------------
Function TaskKill()
    Dim scriptName                  ' �폜�ΏۃX�N���v�g��
    scriptName = "download_new_indicator.vbs"
    Dim computerName                ' �R���s���[�^����
    Dim count                       ' �N���v���Z�X��
    Dim objWMIService               ' WMI
    Dim colItems                    ' wscript����
    Dim objItem                     ' �������ʊi�[
    Dim strcmd                      ' �R�}���h
    Dim killid(299)                  ' �^�X�N�L���Ώۃv���Z�XID
    Dim objShell                    ' �R�}���h���s�p
    Dim i                           ' �J�E���^

    ' �N�����Ă���v���Z�X���擾
    Set objShell = CreateObject("WScript.Shell")
    computerName = "."
    Set objWMIService = GetObject("winmgmts:" & "{impersonationLevel=impersonate}!\\" & computerName & "\root\cimv2")
    
    ' ��L����wscript.exe�������E�擾
    Set colItems = objWMIService.ExecQuery("Select * from Win32_Process Where Name = 'wscript.exe'")
    
    ' �X�N���v�g���̂Ƃ̈�v�����m�����ꍇ�APID���擾
    For Each objItem In colItems
        If InStr(objItem.CommandLine, scriptName) > 0 Then
            killid(count) = objItem.ProcessId
            count = count + 1
        End If
    Next
    
    ' �v���Z�X�̓������s�����m�����ꍇ�A�N�����Ƀ^�X�N�L���R�}���h���s
    If count > 0 Then
        For i = 0 To count - 1
            strcmd = "taskkill /F /T /PID " & killid(i)
            objShell.Exec (strcmd)
        Next
        
'        ' �Ō�Ɏ��g���L������
'        strcmd = "taskkill /F /T /PID " & killid(0)
'        objShell.Exec (strcmd)
    End If
End Function