# Bot Chalane Ka Tarika — Ekdum Aasan (Hinglish)

Ghabrao mat. Poora kaam 4 hisson mein hai. Ek din mein ek hissa karo.

------------------------------------------------------------
## HISSA 1 — PC par 2 software install karo (15 min)
Sirf 2 cheezein download karni hai. Dono FREE hai.

1) **Python** (bot isi par chalta hai)
   - Jao: https://www.python.org/downloads/
   - Bada "Download Python" button dabao → file install karo
   - ⚠️ Install karte waqt niche **"Add Python to PATH"** wale box par TICK zaroor lagana
2) **Git** (code ko GitHub par bhejne ke liye)
   - Jao: https://git-scm.com/download/win
   - Download → install (sab Next-Next dabate jao, kuch change mat karo)

Check karne ke liye: keyboard par Windows button daba ke "cmd" likho, Enter.
Black window khulegi, usme likho:  `python --version`  → Enter.
Agar "Python 3.xx" aaya = ho gaya. ✅

------------------------------------------------------------
## HISSA 2 — 3 FREE chaabiyan (API keys) lo (20 min)
Ye chaabiyan bot ko AI, photo aur video deti hai. Sab muft.

1) **Gemini key** (AI script ke liye)
   - https://aistudio.google.com/apikey
   - Google account se login → "Create API key" → key copy karke kahin notepad me save karo
2) **Pexels key** (free video/photo)
   - https://www.pexels.com/api/ → sign up → key copy karo
3) **Pixabay key** (aur free video/photo)
   - https://pixabay.com/api/docs/ → sign up → key copy karo

Tinon keys ko ek notepad file me likh ke rakho. Baad me kaam aayengi.

------------------------------------------------------------
## HISSA 3 — YouTube par auto-upload ki permission (30 min)
Ye thoda lamba hai, par main saath karwaunga. Abhi sirf itna jaan lo
ki iske baad bot khud video upload karega.
(Steps SETUP_GUIDE.md me hai — Hissa 1 aur 2 ho jaaye to mujhe bolo,
main YouTube wala poora process screen dekh ke karwa dunga.)

------------------------------------------------------------
## HISSA 4 — Bot ko GitHub par daalo (auto chalega 7AM/1PM/6PM)
GitHub ek free website hai jahan code rakhte hai aur wo khud time par
bot chalati hai. Account bana ke code upload karna hota hai — ye bhi
main step-by-step karwaunga jab pehle 3 hisse ho jayein.

------------------------------------------------------------
## Instagram (sabse last me)
Ye tumhare PC se chalega, tumhare ID-password se. Iski tension abhi mat lo.

============================================================
👉 ABHI SIRF ITNA KARO: Upar wala **HISSA 1** (Python + Git install).
Ho jaye to mujhe likho "ho gaya" — main turant HISSA 2 karwa dunga.
============================================================

============================================================
## HISSA 5 — Instagram Reels (tumhare PC se chalega)
============================================================
Cloud har video ke baad ek 1-min ad-reel bana ke `reels_to_post/` folder
mein daal deta hai (hook + "YouTube par poori kahani" + Subscribe end-card).
Tumhare PC par ek script use Instagram par post karta hai. PC par sirf
`instagrapi` chahiye — ffmpeg/video editing PC par NAHI chahiye.

-- EK BAAR ka setup --
1) Sabhi naya code GitHub par bhejo: GitHub Desktop -> Commit -> Push.
2) PC par command window (cmd) kholo project folder mein aur likho:
       pip install instagrapi PyYAML python-dotenv
3) Project folder mein `.env.example` ki copy banao, naam `.env` rakho.
   Usme sirf 2 lines bharo:
       IG_USERNAME=tumhara_instagram_username
       IG_PASSWORD=tumhara_instagram_password
   (Agar Instagram par 2-step verification ON hai to login ke waqt code maangega.)

-- HAR BAAR (ya schedule par) --
4) GitHub Desktop mein "Fetch origin" / "Pull" dabao — naye reels tumhare PC
   ke `reels_to_post/` folder mein aa jayenge.
5) cmd mein likho:
       python src/run_local_instagram.py
   - Jo naye reels hain wo Instagram par post ho jayenge.
   - Jo post ho chuke unhe wo yaad rakhta hai (dobara post nahi karega).
   - Pehli baar login par OTP/challenge aa sakta hai — code daal dena, phir
     session save ho jata hai (aage nahi poochhega).

-- Auto banane ke liye (optional) --
Windows "Task Scheduler" mein `python src/run_local_instagram.py` ko
roz 2-3 baar set kar do (jaise 8AM, 2PM, 7PM). Bas PC us waqt ON ho.

NOTE: Instagram automation thodi sensitive hai. Roz 3 reels theek hai;
isse zyada burst mat karna warna account flag ho sakta hai.

============================================================
## HISSA 6 — Sab kuch kitna automatic hai? + Instagram ko bhi auto karo
============================================================
YouTube videos:  100% AUTOMATIC. Roz 7AM/1PM/6PM par khud banti aur upload
                 hoti hain. Tumhe Actions ya kuch bhi kholne ki zaroorat NAHI.

Instagram reel:  Reel khud ban jata hai. Post karne ke liye PC chahiye.
                 Ise bhi auto karne ke liye (PC ON hona chahiye):

  1) Project folder me `post_reels.bat` file hai (already bani hui).
  2) Windows search -> "Task Scheduler" kholo.
  3) Right side -> "Create Basic Task".
  4) Naam: "Instagram Reels" -> Next.
  5) "Daily" chuno -> Next -> time set karo (jaise 8:00 AM) -> Next.
  6) "Start a program" -> Next -> Browse karke `post_reels.bat` chuno -> Next -> Finish.
  7) (Optional) Din me 3 baar chahiye to aise hi 2 aur task bana lo
     (jaise 2 PM aur 7 PM), thodi der baad video banne ke.

Bas. Ab agar us waqt PC ON hua, to reel khud Instagram par chala jayega.
Pehli baar login par OTP aa sakta hai -> ek baar daal do, phir save ho jata hai.

NOTE: Agar PC us waqt OFF ho, to bs jab next baar `post_reels.bat` chalega
(ya tum manually chalaoge) tab pending reels ek saath post ho jayenge.
