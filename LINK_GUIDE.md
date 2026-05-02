# Open OurHome Link on Any Device

This guide shows you how to run the OurHome website so anyone can open it from their phone, tablet, or laptop using a simple link.

---

## Option 1: Same WiFi / Local Network (Easiest)

Perfect for showing the website to family, friends, or teammates on the same WiFi.

### Step 1: Run the network script

Double-click:
```
Start_Network_Link.bat
```

Or in terminal:
```bash
python run_network.py
```

### Step 2: Open the printed link

You will see something like:
```
==================================================
  OurHome is running on your local network!
==================================================
  Local URL:   http://127.0.0.1:5000
  Network URL: http://192.168.1.5:5000
==================================================
```

**Open `http://192.168.1.5:5000` on any device connected to the same WiFi.**

> Note: The IP address (`192.168.1.5`) will be different on your computer. Use the one shown in the terminal.

---

## Option 2: Public Link (Works Anywhere in the World)

Use this when you want to share the link with someone who is NOT on your WiFi.

### Step 1: Install cloudflared (one-time setup)

1. Download cloudflared for Windows:  
   https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
2. Extract `cloudflared.exe`
3. Place `cloudflared.exe` in this folder (`d:/orphan welfare`)  
   OR add it to your system PATH

### Step 2: Run the public link script

Double-click:
```
Start_Public_Link.bat
```

Or in terminal:
```bash
python run_tunnel.py
```

### Step 3: Share the generated HTTPS link

After a few seconds, you will see:
```
============================================================
  Your public link is ready!
  https://abc123.trycloudflare.com
============================================================
  Share this link with anyone — it works on any device.
  Press CTRL+C to stop the server.
============================================================
```

**Anyone in the world can open `https://abc123.trycloudflare.com` on their phone or laptop, even on mobile data.**

> The link is temporary and changes each time you run the script. It's completely free and requires no account.

---

## Quick Comparison

| Feature | `run_network.py` | `run_tunnel.py` |
|---------|------------------|-----------------|
| Same WiFi only? | Yes | No — works anywhere |
| Needs internet? | No | Yes |
| Needs extra install? | No | cloudflared.exe (one-time) |
| Link changes? | No (your local IP is fixed) | Yes (new each time) |
| Speed | Fast | Depends on internet |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Windows Firewall blocks the app | Click "Allow Access" when the popup appears |
| Phone can't open the link | Make sure both devices are on the **same WiFi** (for Option 1) |
| cloudflared not found | Download it from the link above and place in this folder |
| Port 5000 is busy | Change `port = 5000` to `port = 5001` in the script |

---

## Files Added

- `run_network.py` — runs app on local network (same WiFi)
- `run_tunnel.py` — runs app with a public HTTPS link (anywhere)
- `Start_Network_Link.bat` — double-click to start Option 1
- `Start_Public_Link.bat` — double-click to start Option 2
- `LINK_GUIDE.md` — this guide

