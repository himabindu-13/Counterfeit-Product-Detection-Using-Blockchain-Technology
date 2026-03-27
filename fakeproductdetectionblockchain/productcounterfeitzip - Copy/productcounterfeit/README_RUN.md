# 🚀 How to Run the Product Verification System

## Quick Start (Easiest Way)

### Option 1: Simple Run (No HTTPS)
1. Double-click **`run_app.bat`**
2. Wait for the server to start
3. Open your browser: **http://localhost:5000**
4. Login and test!

**Note:** Camera won't work on mobile with HTTP. Use Option 2 for mobile testing.

---

### Option 2: With HTTPS (For Mobile Camera)
1. Double-click **`run_app_https.bat`**
2. Wait for the server to start
3. On your phone, open: **https://YOUR-IP:5000** (the IP shown in the console)
4. **Accept the security warning** (it's safe - it's a self-signed certificate)
5. Camera will now work on mobile! 📱

---

### Option 3: Manual Run (If scripts don't work)

**Step 1: Open PowerShell/Terminal**
- Press `Windows Key + X`
- Select "Windows PowerShell" or "Terminal"

**Step 2: Go to the project folder**
```powershell
cd "C:\Users\shrav\Documents\fakeproductdetectionblockchain\productcounterfeitzip - Copy\productcounterfeit"
```

**Step 3: Activate virtual environment**
```powershell
.\.venv\Scripts\Activate.ps1
```

**Step 4: Run the app**
```powershell
# Simple run (HTTP)
python app3.py

# OR with HTTPS (for mobile)
$env:FLASK_USE_HTTPS="1"
python app3.py
```

---

## 📱 Testing on Mobile Phone

### Using HTTPS Method (Recommended):

1. **Run `run_app_https.bat`**
2. **Find your computer's IP address** (shown in console, or check manually):
   - Open Command Prompt
   - Type: `ipconfig`
   - Look for "IPv4 Address" (usually like 192.168.1.XX)
3. **On your phone** (same WiFi network):
   - Open browser
   - Go to: `https://YOUR-IP:5000` (e.g., `https://192.168.1.50:5000`)
   - Accept the security warning
   - Login and test camera! 📸

### Using ngrok (Alternative):

1. **Download ngrok** from https://ngrok.com
2. **Run the app normally** (use `run_app.bat`)
3. **In another terminal**, run: `ngrok http 5000`
4. **Copy the HTTPS URL** from ngrok (e.g., `https://abc123.ngrok.io`)
5. **Set environment variable** and restart:
   ```powershell
   $env:PUBLIC_BASE_URL="https://abc123.ngrok.io"
   python app3.py
   ```
6. **On your phone**: Use the ngrok URL

---

## 🔧 Troubleshooting

### Camera not working?
- ✅ Must use HTTPS (not HTTP) for camera on mobile
- ✅ Phone and computer must be on same WiFi
- ✅ Accept the security certificate warning on phone
- ✅ Use `run_app_https.bat` for easiest setup

### "Module not found" error?
- Activate virtual environment: `.\.venv\Scripts\Activate.ps1`
- Install packages: `pip install flask qrcode opencv-python numpy web3 eth-account pyOpenSSL pyzbar`

### Can't access from phone?
- Check Windows Firewall: Allow port 5000
- Make sure phone and computer are on same WiFi network
- Try the ngrok method instead

### QR code scanning not working?
- After setting up HTTPS/ngrok, **regenerate QR codes** from manufacturer dashboard
- New QR codes will have the correct URL

---

## 📝 Default Login

- **Username:** `admin`
- **Password:** `admin123`

---

## 🎯 What Each Role Does

- **Admin:** Manage users and products
- **Manufacturer:** Create products, generate QR codes
- **Vendor:** Purchase and sell products
- **Customer:** Verify products using camera or uploaded images

---

## 💡 Tips

- For development/testing: Use `run_app.bat` (HTTP)
- For mobile testing: Use `run_app_https.bat` (HTTPS)
- For production: Use proper SSL certificates (not self-signed)

---

## ✅ Quick Checklist

Before running:
- [ ] Virtual environment created (`.venv` folder exists)
- [ ] All packages installed
- [ ] Database file exists (`products.db`)

To test mobile:
- [ ] Running with HTTPS
- [ ] Phone on same WiFi
- [ ] Accept certificate on phone
- [ ] QR codes regenerated after setting PUBLIC_BASE_URL

---

**That's it! Double-click `run_app.bat` to start! 🎉**

