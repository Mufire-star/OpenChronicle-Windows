param(
    [int]$Depth = 6,
    [switch]$FocusedWindowOnly
)

$ErrorActionPreference = "Stop"

Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes

function Get-RoleName([System.Windows.Automation.AutomationElement]$Element) {
    $programmatic = $Element.Current.ControlType.ProgrammaticName
    switch ($programmatic) {
        "ControlType.Edit" { return "AXTextField" }
        "ControlType.Document" { return "AXWebArea" }
        "ControlType.Text" { return "AXStaticText" }
        "ControlType.ComboBox" { return "AXComboBox" }
        "ControlType.Button" { return "AXButton" }
        "ControlType.TabItem" { return "AXTab" }
        "ControlType.MenuItem" { return "AXMenuItem" }
        default {
            if ([string]::IsNullOrWhiteSpace($programmatic)) {
                return "AXGroup"
            }
            return "AX" + ($programmatic -replace '^ControlType\.', '')
        }
    }
}

function Get-ElementValue([System.Windows.Automation.AutomationElement]$Element) {
    try {
        $pattern = $Element.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern)
        if ($pattern) {
            return $pattern.Current.Value
        }
    } catch {}
    try {
        return $Element.Current.Name
    } catch {
        return ""
    }
}

function Convert-Element([System.Windows.Automation.AutomationElement]$Element, [int]$Level, [int]$MaxDepth) {
    $role = Get-RoleName $Element
    $title = ""
    try { $title = $Element.Current.Name } catch {}
    $value = Get-ElementValue $Element

    $node = @{
        role = $role
        title = $title
        value = $value
        children = @()
    }

    if ($Level -ge $MaxDepth) {
        return $node
    }

    $walker = [System.Windows.Automation.TreeWalker]::ControlViewWalker
    $children = @()
    try {
        $child = $walker.GetFirstChild($Element)
        $count = 0
        while ($child -and $count -lt 80) {
            $children += ,(Convert-Element $child ($Level + 1) $MaxDepth)
            $child = $walker.GetNextSibling($child)
            $count += 1
        }
    } catch {}
    $node.children = @($children)
    return $node
}

function Get-TopWindow([System.Windows.Automation.AutomationElement]$Element) {
    $walker = [System.Windows.Automation.TreeWalker]::ControlViewWalker
    $current = $Element
    $parent = $null
    while ($true) {
        try {
            $parent = $walker.GetParent($current)
        } catch {
            break
        }
        if (-not $parent) {
            break
        }
        try {
            if ($parent.Current.ControlType.ProgrammaticName -eq "ControlType.Window") {
                $current = $parent
                continue
            }
        } catch {}
        break
    }
    return $current
}

try {
    $focused = [System.Windows.Automation.AutomationElement]::FocusedElement
    if (-not $focused) {
        throw "No focused automation element"
    }

    $window = Get-TopWindow $focused
    $processId = $window.Current.ProcessId
    $proc = Get-Process -Id $processId -ErrorAction Stop
    $elements = @()

    if ($FocusedWindowOnly) {
        $elements += Convert-Element $window 0 $Depth
    } else {
        $elements += Convert-Element $focused 0 $Depth
    }

    $bundleId = $proc.ProcessName
    try {
        if ($proc.Path) {
            $bundleId = $proc.Path
        }
    } catch {}

    $result = @{
        timestamp = [DateTimeOffset]::Now.ToString("o")
        apps = @(
            @{
                name = $proc.ProcessName
                bundle_id = $bundleId
                is_frontmost = $true
                windows = @(
                    @{
                        title = $window.Current.Name
                        focused = $true
                        elements = $elements
                    }
                )
            }
        )
    }

    $result | ConvertTo-Json -Depth 100 -Compress
} catch {
    [Console]::Error.WriteLine($_.Exception.Message)
    exit 1
}
