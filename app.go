package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"sync"
	"time"

	wailsRuntime "github.com/wailsapp/wails/v2/pkg/runtime"
)

// App struct
type App struct {
	ctx    context.Context
	logger *log.Logger
	logFile *os.File
}

// NewApp creates a new App application struct
func NewApp() *App {
	return &App{}
}

// initLogger initializes the log file in the executable directory
func (a *App) initLogger() {
	exePath, err := os.Executable()
	if err != nil {
		fmt.Println("Error getting executable path:", err)
		return
	}
	exeDir := filepath.Dir(exePath)
	logPath := filepath.Join(exeDir, "log.txt")

	// Open file with O_TRUNC to overwrite on each startup
	file, err := os.OpenFile(logPath, os.O_CREATE|os.O_WRONLY|os.O_TRUNC, 0644)
	if err != nil {
		fmt.Println("Error creating log file:", err)
		return
	}

	a.logFile = file
	a.logger = log.New(file, "", 0)
	a.log("=== epub_tool started at %s ===", time.Now().Format("2006-01-02 15:04:05"))
	a.log("Log file: %s", logPath)
}

// log writes a message to the log file
func (a *App) log(format string, args ...interface{}) {
	if a.logger != nil {
		timestamp := time.Now().Format("15:04:05")
		msg := fmt.Sprintf(format, args...)
		a.logger.Printf("[%s] %s", timestamp, msg)
	}
}

// startup is called when the app starts. The context is saved
// so we can call the runtime methods
func (a *App) startup(ctx context.Context) {
	a.ctx = ctx
	a.initLogger()
	
	// Handle file drop
	wailsRuntime.OnFileDrop(ctx, func(x, y int, paths []string) {
		a.log("File drop received: %d files", len(paths))
		for _, p := range paths {
			a.log("  - %s", p)
		}
		wailsRuntime.EventsEmit(a.ctx, "file_drop", paths)
	})
}

// shutdown is called when the app is closing
func (a *App) shutdown(ctx context.Context) {
	a.log("=== epub_tool shutdown ===")
	if a.logFile != nil {
		a.logFile.Close()
	}
}

// SelectFiles opens a file dialog to select EPUB files
func (a *App) SelectFiles() []string {
	selection, err := wailsRuntime.OpenMultipleFilesDialog(a.ctx, wailsRuntime.OpenDialogOptions{
		Title: "选择EPUB文件",
		Filters: []wailsRuntime.FileFilter{
			{
				DisplayName: "EPUB Files",
				Pattern:     "*.epub;*.EPUB",
			},
		},
	})
	if err != nil {
		a.log("Error selecting files: %v", err)
		return []string{}
	}
	a.log("Selected %d files", len(selection))
	return selection
}

// SelectDir opens a directory dialog
func (a *App) SelectDir() string {
	selection, err := wailsRuntime.OpenDirectoryDialog(a.ctx, wailsRuntime.OpenDialogOptions{
		Title: "选择文件夹",
	})
	if err != nil {
		a.log("Error selecting directory: %v", err)
		return ""
	}
	a.log("Selected directory: %s", selection)
	return selection
}

// GetLogContent reads and returns the log file content
func (a *App) GetLogContent() string {
	exePath, err := os.Executable()
	if err != nil {
		return "Error: Unable to get executable path"
	}
	exeDir := filepath.Dir(exePath)
	logPath := filepath.Join(exeDir, "log.txt")

	content, err := os.ReadFile(logPath)
	if err != nil {
		return "Error: Unable to read log file - " + err.Error()
	}
	return string(content)
}

// OpenLogFile opens the log file in the system's default text editor
func (a *App) OpenLogFile() string {
	exePath, err := os.Executable()
	if err != nil {
		return "Error: Unable to get executable path"
	}
	exeDir := filepath.Dir(exePath)
	logPath := filepath.Join(exeDir, "log.txt")

	// Check if file exists
	if _, err := os.Stat(logPath); os.IsNotExist(err) {
		return "Error: Log file does not exist"
	}

	// Open with system default application
	var cmd *exec.Cmd
	switch runtime.GOOS {
	case "darwin":
		cmd = exec.Command("open", logPath)
	case "windows":
		cmd = exec.Command("notepad", logPath)
	default:
		cmd = exec.Command("xdg-open", logPath)
	}

	if err := cmd.Start(); err != nil {
		return "Error: Unable to open log file - " + err.Error()
	}

	a.log("Opened log file: %s", logPath)
	return logPath
}

type TaskResult struct {
	Status     string `json:"status"`
	Message    string `json:"message"`
	File       string `json:"file"`
	OutputPath string `json:"output_path"`
}

// RunTask executes the python script for the given files - now with parallel processing
func (a *App) RunTask(files []string, command string, outputDir string, extraJson string) {
	go func() {
		a.log("Starting task: %s with %d files", command, len(files))
		startTime := time.Now()

		// Determine paths once
		exePath, err := os.Executable()
		if err != nil {
			a.log("Error getting executable path: %v", err)
			wailsRuntime.EventsEmit(a.ctx, "task_log", fmt.Sprintf("Error getting executable path: %v", err))
			return
		}
		exeDir := filepath.Dir(exePath)

		sidecarName := "epub_tool_backend"
		if runtime.GOOS == "windows" {
			sidecarName += ".exe"
		}
		sidecarPath := filepath.Join(exeDir, sidecarName)

		// Check if sidecar exists
		useSidecar := true
		if _, err := os.Stat(sidecarPath); err != nil {
			useSidecar = false
			a.log("Sidecar not found, using python3 fallback")
		} else {
			a.log("Using sidecar: %s", sidecarPath)
		}

		// Determine python script path for fallback mode
		// Try multiple locations: next to executable, in Resources folder (macOS), or project root
		var scriptPath string
		possiblePaths := []string{
			filepath.Join(exeDir, "python_core", "cli.py"),
			filepath.Join(exeDir, "..", "Resources", "python_core", "cli.py"), // macOS .app bundle
			filepath.Join(exeDir, "..", "..", "..", "python_core", "cli.py"),  // Development: go up from .app/Contents/MacOS
			"python_core/cli.py", // Fallback to relative path
		}
		for _, p := range possiblePaths {
			if _, err := os.Stat(p); err == nil {
				scriptPath = p
				break
			}
		}
		if scriptPath == "" {
			scriptPath = possiblePaths[len(possiblePaths)-1] // Use relative as last resort
		}
		if !useSidecar {
			a.log("Python script path: %s", scriptPath)
		}

		// Concurrency control - limit parallel workers
		maxWorkers := runtime.NumCPU()
		if maxWorkers > 4 {
			maxWorkers = 4 // Cap at 4 to avoid overwhelming the system
		}
		a.log("Using %d parallel workers", maxWorkers)
		
		sem := make(chan struct{}, maxWorkers)
		var wg sync.WaitGroup
		var progressMu sync.Mutex
		completed := 0
		total := len(files)

		for _, file := range files {
			wg.Add(1)
			sem <- struct{}{} // Acquire semaphore

			go func(file string) {
				defer wg.Done()
				defer func() { <-sem }() // Release semaphore

				fileStart := time.Now()
				a.log("Processing: %s", filepath.Base(file))
				wailsRuntime.EventsEmit(a.ctx, "task_log", fmt.Sprintf("Processing %s...", filepath.Base(file)))

				var cmd *exec.Cmd
				if useSidecar {
					cmdArgs := []string{command, "--input", file, "--extra", extraJson}
					if outputDir != "" {
						cmdArgs = append(cmdArgs, "--output", outputDir)
					}
					cmd = exec.Command(sidecarPath, cmdArgs...)
				} else {
					pythonCmd := "python3"
					cmdArgs := []string{scriptPath, command, "--input", file, "--extra", extraJson}
					if outputDir != "" {
						cmdArgs = append(cmdArgs, "--output", outputDir)
					}
					cmd = exec.Command(pythonCmd, cmdArgs...)
				}

				output, err := cmd.CombinedOutput()
				elapsed := time.Since(fileStart)

				if err != nil {
					a.log("Error processing %s: %v (took %v)", filepath.Base(file), err, elapsed)
					wailsRuntime.EventsEmit(a.ctx, "task_result", TaskResult{
						Status:  "error",
						File:    file,
						Message: fmt.Sprintf("Error: %v. Output: %s", err, string(output)),
					})
					wailsRuntime.EventsEmit(a.ctx, "task_log", fmt.Sprintf("Error: %s - %v", filepath.Base(file), err))
				} else {
					var result TaskResult
					if err := json.Unmarshal(output, &result); err != nil {
						a.log("Completed: %s (took %v)", filepath.Base(file), elapsed)
						wailsRuntime.EventsEmit(a.ctx, "task_result", TaskResult{
							Status:  "success",
							File:    file,
							Message: string(output),
						})
						wailsRuntime.EventsEmit(a.ctx, "task_log", fmt.Sprintf("Done: %s", filepath.Base(file)))
					} else {
						// 记录完成日志，包含输出路径（如果可用）
						if result.OutputPath != "" {
							a.log("Completed: %s -> %s (took %v)", filepath.Base(file), result.OutputPath, elapsed)
						} else {
							a.log("Completed: %s (took %v)", filepath.Base(file), elapsed)
						}
						wailsRuntime.EventsEmit(a.ctx, "task_result", result)
						logMsg := fmt.Sprintf("Done: %s", filepath.Base(file))
						if result.OutputPath != "" {
							logMsg += fmt.Sprintf("\nOutput: %s", result.OutputPath)
						}
						wailsRuntime.EventsEmit(a.ctx, "task_log", logMsg)
					}
				}

				// Update progress
				progressMu.Lock()
				completed++
				wailsRuntime.EventsEmit(a.ctx, "task_progress", map[string]interface{}{
					"current": completed,
					"total":   total,
				})
				progressMu.Unlock()
			}(file)
		}

		wg.Wait()
		totalElapsed := time.Since(startTime)
		a.log("Task completed: %s - processed %d files in %v", command, total, totalElapsed)
		wailsRuntime.EventsEmit(a.ctx, "task_complete", "done")
	}()
}
