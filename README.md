# Supplement Tracker

A Python application to track your supplements, their quantities, and calculate cost effectiveness.

## Features

- Add, edit, and remove supplements
- Track supplement quantities and daily usage
- Calculate days remaining for each supplement
- Search through supplements by name or tags
- Cost calculator to compare different supplement options
- Automatic tracking of remaining doses based on daily usage
- Toggle auto-decrement feature for each supplement
- Right-click context menu for quick actions
- Keyboard shortcuts for common operations
- Visual feedback for supplements with auto-decrement disabled
- Helpful tooltips for better user experience
- Save and load data with custom .sup file format
- Automatic count updates based on time passed since last save and whenever the supplement list is refreshed
- Windows file association for .sup files
- Drag and drop support for .sup files
- Available as both Python script and standalone executable

## Installation

### Option 1: Running from Python (Development)

1. Make sure you have Python 3.x installed
2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

### Option 2: Using the Executable (Recommended for most users)

1. Download the latest SupplementTracker.exe from the releases
2. Run the executable once with --register to set up file associations:
```bash
SupplementTracker.exe --register
```

### Building the Executable Yourself

1. Install Python 3.x and the requirements:
```bash
pip install -r requirements.txt
```

2. Run the build script:
```bash
python build.py
```

3. Find the executable in the 'dist' directory
4. Run the executable with --register to set up file associations:
```bash
SupplementTracker.exe --register
```

## Usage

### Starting the Program

You can start the program in several ways:
1. If using Python: `python main.py`
   If using executable: Run `SupplementTracker.exe`
2. Open with a specific file: 
   - Python: `python main.py myfile.sup`
   - Executable: `SupplementTracker.exe myfile.sup`
3. Double-click any .sup file (after registering file association)
4. Drag and drop a .sup file onto the program

### Adding a Supplement

1. Click "Add Supplement"
2. Fill in the required information:
   - Name: Supplement name
   - Current Count: Current number of doses
   - Initial Count: Number of doses when bought
   - Cost: Price of the supplement
   - Tags: Comma-separated tags (e.g., "vitamin, mineral")
   - Link: URL to the product (optional)
   - Daily Dose: Number of doses taken per day
   - Auto-decrement: Toggle whether the supplement count should automatically decrease daily (checked by default)

### Editing a Supplement

You can edit a supplement in multiple ways:
1. Right-click on a supplement and select "Edit" from the context menu
2. Select a supplement and press Enter
3. Double-click on a supplement

The edit dialog allows you to modify all supplement properties, including the auto-decrement setting.

### Using Keyboard Shortcuts

The application supports several keyboard shortcuts for common actions:
- **Ctrl+S**: Save the current file
- **Enter**: Edit the selected supplement
- **Delete**: Remove the selected supplement
- **Ctrl+A**: Select all supplements
- **Escape**: Clear selection

### Using the Cost Calculator

1. Click "Cost Calculator"
2. Add options using the "Add Option" button
3. For each option, enter:
   - Dose Count: Number of doses in the package
   - Price: Total price of the package
   - Daily Dose: Number of doses taken per day
4. Click "Calculate" to see cost comparison
5. Use the "Remove" button to remove unwanted options (minimum 2 required)

### Managing Files

- Use "Save As..." to save your data to a new .sup file
- Use "Load File" to open an existing .sup file
- The program automatically tracks the save date and updates counts based on time passed whenever a file is loaded or the supplement list is refreshed
- When closing, you'll be prompted to save any unsaved changes
- Press Ctrl+S to quickly save your current file

### Searching

Use the search box to filter supplements by name or tags.

### Visual Indicators

Supplements with auto-decrement disabled are visually distinguished in the list, making it easy to identify which supplements are not automatically decreasing their count.

## Data Storage

The application saves all supplement data to .sup files (JSON format). These files include:
- Supplement details (name, count, cost, etc.)
- Save date for automatic count updates
- Tags and links
- Daily dosage information
- Auto-decrement settings for each supplement

The program automatically updates supplement counts based on the time passed since the last save when loading a file, but only for supplements that have auto-decrement enabled.

## Backward Compatibility

The application maintains backward compatibility with older .sup files that don't include the auto-decrement property. When loading such files, all supplements will have auto-decrement enabled by default. 