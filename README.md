🗂️ Smart Organizer Pro v5

Smart Organizer Pro v5 is a Python desktop application that automatically organizes and backs up your files. It includes manual backup, scheduled automation, and system tray integration for seamless operation.

✨ Features

🖱️ Manual Backup – Backup selected folders instantly

⏰ Scheduled Backup – Run every hour or daily at a specific time

🧩 Duplicate Detection – Prevent copying duplicate files using MD5 hashes

📂 Smart Folder Organization – Automatically sorts files by type and creation date

📊 Real-Time Logs & Progress – Monitor backup activity live

🖥️ System Tray Integration – Keep the app running in the background

⚡ Installation

Clone the repository:

git clone https://github.com/TuanBulut/SmartOrganizer.git
cd SmartOrganizer


Create a virtual environment and install dependencies:

python -m venv .venv
# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt

🚀 Usage

Run the application:

python smart_file_organizer_pro_v5.py


Select your source folder and backup folder

Click Manual Backup to run immediately

Go to Automation to schedule backups

Minimize to tray to let it run in the background

🛠️ Dependencies

customtkinter

pystray

pillow

pyinstaller

darkdetect

pywin32-ctypes

(See requirements.txt for full list)

📝 License

This project is licensed under the MIT License – see LICENSE
 for details.
