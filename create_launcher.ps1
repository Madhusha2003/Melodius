$code = @"
using System;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;

public class Launcher {
    [DllImport("kernel32.dll")]
    static extern bool FreeConsole();

    public static void Main() {
        FreeConsole();
        
        string baseDir = AppDomain.CurrentDomain.BaseDirectory;
        string pythonPath = Path.Combine(baseDir, "python_11", "pythonw.exe");
        string scriptPath = Path.Combine(baseDir, "melodius_3ports.py");

        // Basic error check
        if (!File.Exists(pythonPath)) {
            System.Windows.Forms.MessageBox.Show("FATAL ERROR: Could not find 'python_11\\pythonw.exe'.\n\nPlease ensure you are running this from the Melodius installation folder.", "Melodius Launcher");
            return;
        }

        ProcessStartInfo startInfo = new ProcessStartInfo();
        startInfo.FileName = pythonPath;
        startInfo.Arguments = "\"" + scriptPath + "\"";
        startInfo.WorkingDirectory = baseDir;
        startInfo.UseShellExecute = false;
        startInfo.CreateNoWindow = true;
        startInfo.WindowStyle = ProcessWindowStyle.Hidden;

        try {
            Process.Start(startInfo);
        } catch (Exception ex) {
            System.Windows.Forms.MessageBox.Show("Error starting Melodius:\n" + ex.Message, "Melodius Launcher");
        }
    }
}
"@

Write-Host "--- Building Melodius Launcher EXE with Icon ---" -ForegroundColor Cyan

$iconPath = "assets\melodius_icon_512.ico"

if (Test-Path $iconPath) {
    # We use CompilerParameters to include the icon
    $params = New-Object System.CodeDom.Compiler.CompilerParameters
    $params.ReferencedAssemblies.AddRange(@("System.dll", "System.Windows.Forms.dll", "System.Drawing.dll"))
    $params.GenerateExecutable = $true
    $params.OutputAssembly = "Melodius.exe"
    $params.CompilerOptions = "/target:winexe /win32icon:`"$iconPath`""
    
try {
    Add-Type -TypeDefinition $code -CompilerParameters $params -ErrorAction Stop
    Write-Host "Success! Melodius.exe has been created with icon: $iconPath" -ForegroundColor Green
} catch {
    Write-Host "Failed to build with icon. Error: $_" -ForegroundColor Red
    # Fallback
    Add-Type -TypeDefinition $code -ReferencedAssemblies "System.Windows.Forms","System.Drawing" -OutputAssembly "Melodius.exe" -OutputType WindowsApplication
    Write-Host "Created Melodius.exe without icon as fallback." -ForegroundColor Yellow
}
} else {
    # Fallback if icon is missing
    Add-Type -TypeDefinition $code -ReferencedAssemblies "System.Windows.Forms","System.Drawing" -OutputAssembly "Melodius.exe" -OutputType WindowsApplication
    Write-Host "Success! Melodius.exe has been created (Icon not found, using default)." -ForegroundColor Yellow
}
