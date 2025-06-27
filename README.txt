SwiftSale™ - User Guide
Last Updated: May 12, 2025

Welcome to SwiftSale™, the ultimate tool for Whatnot sellers to streamline bidder management, track sales, and enhance live show efficiency. Developed by Mike St Pierre, SwiftSale™ reduces show time by up to 57% and post-show processing by 83% through automated bin assignment, real-time analytics, and Telegram notifications. This guide explains how to download, install, and use SwiftSale™ via a desktop application (executable) and/or a web dashboard hosted on Heroku.

---

Table of Contents
1. Overview
2. Features
3. System Requirements
4. Getting Started
   - Installing the Desktop Application
   - Accessing the Web Dashboard
5. Using the Application
   - Desktop GUI
   - Web Dashboard
6. Subscription Management
7. Data Management
8. Troubleshooting
9. License
10. Support and Contact

---

1. Overview
SwiftSale™ is a subscription-based application designed for Whatnot sellers to manage bidders, assign bins, track giveaways, and monitor sales during live shows. It offers a desktop GUI (via a downloadable executable) for rich interaction and a web-based dashboard for real-time updates, hosted on Heroku. With integrations for Stripe (subscriptions) and Telegram (notifications), SwiftSale™ supports multiple subscription tiers (Trial, Bronze, Silver, Gold) to suit sellers of all scales.

---

2. Features
- Bidder Management: Assign bins or giveaway numbers, track purchases, and manage bidder data.
- Real-Time Analytics: Monitor top buyers and average sell rate (items/hour) during shows.
- Subscription Tiers: Access Trial (20 bins), Bronze (50 bins), Silver (150 bins), or Gold (300 bins) via Stripe.
- Telegram Notifications: Receive instant bin assignment updates in Telegram chats.
- Desktop GUI: Use a user-friendly interface for bidder management and analytics (via executable).
- Web Dashboard: View live bin assignments and manage subscriptions online.
- Data Persistence: Store subscriptions and settings securely in a production database.

---

3. System Requirements
- **Desktop GUI (Executable)**:
  - Operating System: Windows 10/11 (macOS/Linux versions available upon request).
  - Disk Space: ~100 MB for the application.
  - Internet: Required for Stripe subscriptions and Telegram notifications.
- **Web Dashboard**:
  - Browser: Modern browser (e.g., Chrome, Firefox, Safari) with JavaScript enabled.
  - Internet: Stable connection for accessing the Heroku-hosted app and Stripe/Telegram services.
- **Account**:
  - SwiftSale™ account (email-based, provided upon subscription).
  - Stripe account for subscription payments.
  - Telegram account for notifications (optional).

---

4. Getting Started
SwiftSale™ is available as a downloadable desktop application (Windows executable) and a web dashboard hosted on Heroku. Follow these steps to start using SwiftSale™.

4.1 Installing the Desktop Application
- **Download**:
  - Visit [Insert Download Link, e.g., https://swiftsaleapp.com/download] to download SwiftSale.exe.
  - Save the file to a convenient location (e.g., Desktop or Downloads).
- **Install**:
  - Double-click SwiftSale.exe to launch the application.
  - Windows may prompt for permission; click "Run" or allow through Windows Defender.
  - No additional installation is required, as the executable includes all dependencies and the SwiftSale™ logo.
- **Notes**:
  - Ensure an internet connection for initial setup (subscription and Telegram).
  - The logo (swiftsale_logo.png) is bundled with the executable and displays in the GUI header.
  - For macOS/Linux, contact support for alternative executables.

4.2 Accessing the Web Dashboard
- **URL**: Open your browser and navigate to:
  https://your-swiftsale-app.herokuapp.com
  (Replace with the actual URL provided by your SwiftSale™ administrator.)
- **Login**:
  - Enter your registered email address (set during subscription).
  - No password is required; authentication is email-based.
- **Notes**:
  - Requires JavaScript enabled for Stripe and real-time updates.
  - Accessible from any device with a browser.

4.3 Setting Up Telegram Notifications (Optional)
- Create a Telegram bot via BotFather (https://t.me/BotFather) to obtain a bot token.
- Join or create a Telegram chat and get the chat ID (use a bot like @GetIDBot).
- Enter the bot token and chat ID in the application’s settings (see Section 5).

---

5. Using the Application

5.1 Desktop GUI
- **Launch**: Double-click SwiftSale.exe to start the application.
- **Interface**:
  - **Header**: Displays your email and subscription tier (e.g., "SwiftSale - your_email@example.com (Trial)") with the SwiftSale™ logo.
  - **Add Bidder**:
    - Enter username, quantity, weight (optional), and check "Giveaway" if applicable.
    - Click "Add Bidder" to assign a bin or giveaway number.
  - **Settings**:
    - Input Telegram Chat ID and custom texts (e.g., top buyer, giveaway announcements).
    - Click "Save Settings" to store preferences.
  - **Subscription**:
    - Select a tier (Trial, Bronze, Silver, Gold) and click "Upgrade," "Downgrade," or "Cancel."
    - Follow the Stripe checkout link in your browser.
  - **Analytics**:
    - View top buyers and sell rate (items/hour).
    - Click "Start Show" to begin tracking sell rate.
  - **Bidders**:
    - Click "Print Bidders" to display all bidders.
    - Use "Import CSV" or "Export CSV" for data management.
    - Click "Clear Bidders" to reset.
- **Notes**:
  - Requires an internet connection for Stripe and Telegram.
  - The GUI runs on Windows; contact support for macOS/Linux versions.

5.2 Web Dashboard
- **URL**: https://your-swiftsale-app.herokuapp.com
- **Features**:
  - View real-time bin assignments (updated via SocketIO).
  - Manage subscriptions (upgrade, downgrade, cancel) through Stripe checkout.
- **Usage**:
  - Log in with your email.
  - Monitor the latest bin assignments on the dashboard.
  - Click subscription buttons (e.g., "Upgrade to Bronze") to manage your tier.
- **Notes**:
  - Best for quick access or mobile use.
  - Requires a modern browser with JavaScript enabled.

---

6. Subscription Management
- **Tiers**:
  - Trial: 20 bins, free evaluation.
  - Bronze: 50 bins, entry-level paid tier.
  - Silver: 150 bins, mid-tier for growing sellers.
  - Gold: 300 bins, premium for large-scale sellers.
- **Managing Subscriptions**:
  - Desktop GUI: Use the "Subscription" section to select a tier and manage via Stripe.
  - Web Dashboard: Click subscription buttons to upgrade/downgrade via Stripe.
  - Cancel: Select "Cancel" to revert to Trial (ends billing).
- **Payment**:
  - Processed securely via Stripe.
  - Follow the checkout link to enter payment details.
- **Notes**:
  - An active subscription is required for Full Mode features.
  - Contact support for billing issues.

---

7. Data Management
- **Production Database**:
  - SwiftSale™ uses a secure PostgreSQL database hosted on Heroku to store subscriptions, settings, and bidder data.
  - Data includes your email, subscription tier, license key, Telegram settings, and custom texts.
- **Data Access**:
  - Managed automatically by the application.
  - Users cannot directly access the database; contact support for data requests.
- **Backup**:
  - Export bidder data via the GUI or web dashboard ("Export CSV" feature).
  - Regular backups are handled by the SwiftSale™ team.
- **Notes**:
  - Ensure your email is correct for subscription tracking.
  - Data is stored in compliance with privacy laws.

---

8. Troubleshooting
- **Desktop GUI Issues**:
  - **Fails to Launch**: Ensure SwiftSale.exe is downloaded from the official source and your OS is Windows 10/11. Try re-downloading or running as administrator.
  - **Logo Missing**: The logo is bundled; contact support if it does not display.
  - **Internet Errors**: Verify your connection for Stripe and Telegram functionality.
- **Web Dashboard Issues**:
  - **Cannot Access**: Check the URL (https://your-swiftsale-app.herokuapp.com) and internet connection.
  - **Subscription Errors**: Ensure JavaScript is enabled and verify payment status in the Stripe dashboard.
- **Telegram Notifications**:
  - **Not Receiving**: Confirm bot token and chat ID in settings. Ensure the bot is not blocked.
- **General**:
  - Check your subscription status in the GUI or dashboard.
  - Contact support with error details (e.g., screenshots, error messages).

---

9. License
SwiftSale™ is licensed under the SwiftSale™ Software License Agreement (see LICENSE.txt included with the executable or web app). Key points:
- Non-exclusive, non-transferable license for personal or commercial use (Full Mode requires an active subscription).
- No modification, distribution, or reverse-engineering allowed.
- Provided "AS IS" with no warranties.
- Owned by Mike St Pierre, including the SwiftSale™ trademark.

Contact support for a copy of LICENSE.txt if not included.

---

10. Support and Contact
For assistance, contact the SwiftSale™ team:
- Email: support@swiftsaleapp.com
- Address: [Insert Physical Address, e.g., 123 SwiftSale Lane, Los Angeles, CA 90001, USA]
- Website: [Insert Website, e.g., https://swiftsaleapp.com]

Include your email, subscription tier, and issue details when contacting support.

---

© 2025 Mike St Pierre. All rights reserved. SwiftSale™ is a trademark of Mike St Pierre.