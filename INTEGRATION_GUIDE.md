# 🌐 Website Integration Guide (www.type4u.qzz.io)

Aapni website par Passport Photo tool ko add karne ke liye, ye Iframe code apne HTML page mein wahan paste karein jahan aap app dikhana chahte hain:

```html
<div style="width: 100%; height: 800px; border-radius: 20px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
    <iframe 
        src="https://typevc.pythonanywhere.com/" 
        style="width: 100%; height: 100%; border: none;"
        title="Passport Photo Pro">
    </iframe>
</div>
```

---

### 🔒 Security Check:
1. **Password:** Jab aap ye page apni website par kholenge, toh wo aapse **Password** mangega. Bina password ke koi use nahi kar payega.
2. **Default Password:** `1234`
3. **Password Badalne Ke Liye:** `app.py` mein line 18 par `APP_PASSWORD = '1234'` ko badal dein.

### 🚀 Final Deployment Checklist:
1. `PYTHONANYWHERE_FIX.txt` mein di gayi commands ko PythonAnywhere console mein run karein.
2. PythonAnywhere ke **Web** tab mein **Reload** button dabayein.
3. Apni website par upar wala Iframe code paste karein.

Aapki app ab password-protected hai aur aapki website par chalne ke liye taiyaar hai!
