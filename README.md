# 🗂️ Smart Organizer Pro v5
[![Ask DeepWiki](https://devin.ai/assets/askdeepwiki.png)](https://deepwiki.com/TuanBulut/SmartOrganizer)

> Effortlessly organize, sort, and back up your files with automation and smart features.

---

## ✨ Features

| Feature                | Description                                                |
| ---------------------- | ---------------------------------------------------------- |
| 🖱️ **Manual Backup**    | Instantly back up selected folders with a single click.    |
| ⏰ **Scheduled Backup**  | Run backups automatically every hour or at a specific time daily. |
| 🧩 **Duplicate Detection** | Avoids redundant copies by using MD5 hash verification to skip existing files. |
| 📂 **Smart Organization**    | Automatically sorts backed-up files into folders by file type and creation date (`YYYY-MM-DD`). |
| 📊 **Real-Time Logs**    | Monitor all backup activities, file copies, and skipped duplicates live. |
| 🖥️ **System Tray Support** | Keep the application running quietly in the background. Closing the window minimizes it to the tray. |

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- `pip` (Python package installer)

### Installation

1.  **Clone the repository:**
    ```sh
    git clone https://github.com/TuanBulut/SmartOrganizer.git
    cd SmartOrganizer
    ```

2.  **Create and activate a virtual environment:**
    - On Windows:
        ```sh
        python -m venv venv
        .\venv\Scripts\activate
        ```
    - On macOS/Linux:
        ```sh
        python3 -m venv venv
        source venv/bin/activate
        ```

3.  **Install the required dependencies:**
    ```sh
    pip install -r requirements.txt
    ```

4.  **Run the application:**
    ```sh
    python smart_file_organizer_pro_v5.py
    ```

## 📖 How to Use

### 1. Initial Setup

Before running any backup, you must configure the source and destination folders on the **Manual Backup** tab.

1.  **Source Folder**: Click `Browse` to select the folder containing the files you want to back up.
2.  **Backup Folder**: Click `Browse` to select the folder where the backups will be stored.

> **Note:** For safety, the application prevents you from setting the backup folder to be the same as the source folder or inside the source folder.

### 2. Manual Backup

For a one-time backup:

1.  Ensure your Source and Backup folders are set.
2.  Click the **Run Backup Now** button.
3.  Monitor the progress bar and the "Recent Log" panel for live updates.
4.  To interrupt the process, click the **Stop Backup** button that appears.

### 3. Automated Backup

To set up a recurring backup schedule:

1.  Navigate to the **Automation** tab.
2.  Choose a schedule from the dropdown menu: `Run every hour` or `Run every day at...`.
3.  If you select the daily option, specify the hour (0-23).
4.  Click **Start Schedule**. The application will now perform backups automatically.
5.  To turn off the schedule, click **Stop Schedule**.

### 4. Running in the Background (System Tray)

-   Closing the main window with the `X` button will not quit the application. Instead, it will minimize to the system tray, allowing scheduled backups to continue running.
-   Right-click the tray icon to `Show` the window again or to `Quit` the application completely.

## 🛠️ Building the Executable

This project is configured to be built into a standalone executable using PyInstaller.

1.  **Install PyInstaller:**
    ```sh
    pip install pyinstaller
    ```

2.  **Run the build command from the project's root directory:**
    ```sh
    pyinstaller smart_file_organizer_pro_v5.spec
    ```

3.  The final executable will be located in the newly created `dist` directory.

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
