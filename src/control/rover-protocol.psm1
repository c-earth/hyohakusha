# Stateless reply validation shared by the PowerShell controllers.
class RoverReply {
    static [void] ThrowIfFault([string]$Frame) {
        $fault = [regex]::Match($Frame, '\{(?:(.*?)_)?error_([a-z0-9_]+)\}')
        if ($fault.Success) {
            $tag = $fault.Groups[1].Value
            if (-not $tag) { $tag = 'untagged' }
            throw [InvalidOperationException]::new("Firmware fault ($tag): $($fault.Groups[2].Value)")
        }
    }
}
