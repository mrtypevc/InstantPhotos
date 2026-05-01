# 🚀 PythonAnywhere Deployment Guide

Aapne PythonAnywhere account bana liya hai, bahut achha! Ab apni Passport Photo App ko live karne ke liye ye steps follow karein:

### 1. Files Upload Karein (Zip Method)
Agar aapke paas saari files ki ek **Zip file** hai, toh ye sabse aasaan hai:
1. PythonAnywhere dashboard par **"Files"** tab par jayein.
2. **"Upload a file"** button par click karke apni Zip file upload karein.
3. Dashboard par **"Consoles"** tab par jayein aur **Bash** console kholein.
4. Ye command likhein (apni zip file ka sahi naam likhein):
   ```bash
   unzip filename.zip -d passport-app
   ```
   (Isse `passport-app` naam ka folder ban jayega aur saari files usmein nikal jayengi).

### 2. Web App Setup Karein
1. **"Web"** tab par jayein aur **"Add a new web app"** par click karein.
2. Select: **Flask** -> **Python 3.10** (ya latest).
3. Jab wo raasta (path) pooche, toh ye daalein: `/home/TypeVC/passport-app/app.py`.

### 3. Dependencies Install Karein
1. Dashboard par **"Consoles"** tab par jayein aur ek naya **Bash** console kholein.
2. Ye command type karein:
   ```bash
   pip3 install -r /home/TypeVC/passport-app/requirements.txt --user
   ```

### 4. WSGI File Config Karein (Sabse Zaroori)
1. **"Web"** tab par wapas jayein.
2. "Code" section mein **"WSGI configuration file"** ke link par click karein.
3. Purana saara code mita dein aur ye naya code daalein:
   ```python
   import sys
   import os
   from dotenv import load_dotenv

   path = '/home/TypeVC/passport-app'
   if path not in sys.path:
       sys.path.append(path)

   os.chdir(path)
   load_dotenv(os.path.join(path, '.env'))

   from app import app as application
   ```
4. File ko **Save** karein.

### 5. Finish
1. **"Web"** tab par wapas jayein aur sabse upar bane bade hare (green) button **"Reload TypeVC.pythonanywhere.com"** par click karein.

🎉 **Mubarak ho!** Aapki website ab live hai: `http://TypeVC.pythonanywhere.com`

---

### Ek Zaroori Baat (Free Plan Limitation)
Kyunki aap free plan par hain, PythonAnywhere bahar ki websites (jaise Cloudinary aur remove.bg) se connect karne ke liye **Proxy** mangta hai. Agar AI features kaam na karein, toh aapko unka $5 wala "Hacker" plan lena pad sakta hai, ya phir humein kuch changes karne honge.
