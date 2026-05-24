# Standalone Bokun & Google Sheets Automation

This package connects your Bokun API with Google Sheets and the Vatican Bot. It allows you to automatically:
1. Fetch participant data from Bokun bookings.
2. Store that data in a Google Sheet for the bot to use.
3. Automatically create monitoring tasks in the bot for new bookings.

## 🚀 Setup Instructions

### 1. Requirements
Ensure you have Python installed on your computer.

### 2. Install Dependencies
Run the following command in your terminal:
```bash
pip install -r requirements.txt
```

### 3. Google Sheets Setup
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a **Service Account**.
3. Create a **JSON Key** for the Service Account and download it.
4. Rename the downloaded file to `google_credentials.json` and place it in this folder.
5. Open your Google Sheet and **Share** it with the email address of your Service Account (found in the JSON file).

### 4. Configuration
The `config.json` file is already pre-configured with your keys. You can adjust the `bot` -> `api_url` if your bot is running on a different server.

### 5. Run the Automation
To sync Bokun with Google Sheets and create bot tasks, run:
```bash
python bokun_to_sheets.py
```

## 🔄 How it Works
- The script fetches **Confirmed** bookings from the next 30 days.
- It extracts participant names, emails, and phone numbers.
- It appends them to the sheet specified in `config.json` (avoiding duplicates by Booking ID).
- It calls the bot's API to create a `snipe` task for the booking date and visitor count.

## ⚠️ Notes
- Ensure the bot is running if you want tasks to be created automatically.
- The sheet name must match exactly what is in `config.json` (Default: `Vatican_Participants`).
