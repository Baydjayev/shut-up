<!doctype html>
<html lang="uz">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>MuteGuardian — Telegram Moderation Bot</title>
  <style>
    :root{
      --bg:#0f1720;
      --card:#0b1220;
      --accent:#2563eb;
      --muted:#9ca3af;
      --white:#ffffff;
      --danger:#ef4444;
      --gap:18px;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial;
    }
    body{
      margin:0;
      background:linear-gradient(180deg,#07121a 0%, #0b1420 100%);
      color:var(--white);
      -webkit-font-smoothing:antialiased;
      -moz-osx-font-smoothing:grayscale;
      padding:40px;
    }
    .container{
      max-width:960px;
      margin:0 auto;
      background:linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
      border-radius:12px;
      padding:28px;
      box-shadow:0 6px 30px rgba(2,6,23,0.6);
      border:1px solid rgba(255,255,255,0.03);
    }
    header{
      display:flex;
      gap:16px;
      align-items:center;
    }
    .logo{
      width:120px;
      height:67.5px; /* keep 16:9 ratio inside 640x360 */
      background:transparent;
      border-radius:8px;
      overflow:hidden;
      box-shadow:0 4px 18px rgba(0,0,0,0.6);
      flex:0 0 120px;
    }
    .logo img{ width:100%; height:100%; object-fit:cover; display:block; }
    h1{ margin:0; font-size:22px; letter-spacing:0.2px; }
    p.lead{ margin:6px 0 0; color:var(--muted); font-size:14px; }

    section{ margin-top:var(--gap); }

    .grid{ display:grid; grid-template-columns:1fr 320px; gap:20px; align-items:start; }
    .card{
      background:rgba(255,255,255,0.02);
      border-radius:10px;
      padding:18px;
      border:1px solid rgba(255,255,255,0.02);
    }
    h2{ margin:0 0 10px 0; font-size:18px; }
    ul{ margin:8px 0 0 18px; color:var(--muted); }
    pre{
      background:#071824;
      padding:12px;
      border-radius:8px;
      overflow:auto;
      color:#d1fae5;
      font-size:13px;
      margin:12px 0;
    }
    .badge{ display:inline-block; padding:6px 10px; border-radius:999px; background:rgba(255,255,255,0.03); color:var(--muted); font-size:13px; }
    footer{ margin-top:22px; color:var(--muted); font-size:13px; text-align:center; }
    .note{ color:var(--muted); font-size:13px; margin-top:8px; }
    .danger{ color:var(--danger); font-weight:600; }
    .center{ text-align:center; }
    a{ color:var(--accent); text-decoration:none; }
    code{ background:rgba(255,255,255,0.03); padding:2px 6px; border-radius:6px; color:var(--white); font-size:13px; }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="logo">
        <!-- Put file shut_up_resized_640x360.jpg in repo root -->
        <img src="shut_up_resized_640x360.jpg" alt="MuteGuardian Logo">
      </div>
      <div>
        <h1>MuteGuardian — Telegram Moderation Bot</h1>
        <p class="lead">Assalomu alaykum, botimizga xush kelibsiz! Guruhingizni toza va tartibli saqlash uchun avtomatik moderatsiya.</p>
      </div>
    </header>

    <section class="grid" aria-label="main">
      <div>
        <div class="card">
          <h2>✨ Asosiy funksiyalar</h2>
          <ul>
            <li>❌ Taqiqlangan so‘zlarni aniqlaydi va xabarni avtomatik o‘chiradi.</li>
            <li>⏳ Qoidabuzarlarga progressiv jazolar: 1–3 martada vaqtinchalik blok (muddat config bo‘yicha), 4-martada guruhdan chiqarish (kick).</li>
            <li>🔄 24 soat ichidagi buzilishlarni hisoblab boradi.</li>
            <li>📩 Foydalanuvchiga xususiy ogohlantirish yuboradi (sababi va blok muddati bilan).</li>
            <li>📢 Guruhga blok haqida xabar yuboradi — keyin avtomatik o‘chiriladi.</li>
            <li>🔕 Guruhga qo‘shilish/chiqish xabarlarini o‘chiradi (kerakli bo‘lsa).</li>
            <li>✅ Botdan foydalanish uchun majburiy kanal obunasi funksiyasi mavjud.</li>
          </ul>
        </div>

        <div class="card" style="margin-top:16px;">
          <h2>⚙️ O‘rnatish</h2>
          <p class="note">Quyidagi buyruqlarni loyihangiz papkasida bajarish kifoya:</p>
          <pre><code>git clone https://github.com/&lt;username&gt;/&lt;repo-name&gt;.git
cd &lt;repo-name&gt;
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux / Mac:
source venv/bin/activate
pip install -r requirements.txt
</code></pre>

          <p class="note">`.env` faylni yarating va ichiga:</p>
          <pre><code>BOT_TOKEN=your_bot_token_here</code></pre>

          <p class="note">Botni ishga tushirish:</p>
          <pre><code>python main.py</code></pre>
        </div>

        <div class="card" style="margin-top:16px;">
          <h2>🧩 Fayl tuzilishi (tavsiya)</h2>
          <ul>
            <li><code>main.py</code> / <code>bot.py</code> — asosiy bot logikasi</li>
            <li><code>config.py</code> — sozlamalar (FORBIDDEN_WORDS, PUNISHMENT_DURATIONS, va hok.)</li>
            <li><code>requirements.txt</code> — dependency ro‘yxati (aiogram, python-dotenv, Pillow va boshqalar)</li>
            <li><code>README.html</code> — bu fayl</li>
            <li><code>shut_up_resized_640x360.jpg</code> — logotip (repo root)</li>
          </ul>
        </div>
      </div>

      <aside>
        <div class="card center">
          <div class="badge">README</div>
          <h2 style="margin-top:12px;">Tez boshlash</h2>
          <p class="note">Kerakli o‘zgartirishlarni <code>config.py</code> ichida bajaring:</p>
          <pre><code>FORBIDDEN_WORDS = ["so'kinish1","so'kinish2","yomonso'z"]
PUNISHMENT_DURATIONS = {1:300, 2:900, 3:3600, 4:86400}
VIOLATION_WINDOW = 86400</code></pre>
          <p class="note">Bot 1–3 marta jarimalar uchun vaqtinchalik blok beradi, 4-martadan keyin <span class="danger">guruhdan chiqaradi</span> (kick).</p>
        </div>

        <div class="card" style="margin-top:16px;">
          <h2>📝 Litsenziya</h2>
          <p class="note">MIT License — ochiq manba. O‘zgartirish va tarqatish mumkin.</p>
        </div>

        <div class="card" style="margin-top:16px;">
          <h2>📬 Aloqa</h2>
          <p class="note">Muammo yoki takliflar uchun GitHub Issues orqali murojaat qiling.</p>
        </div>
      </aside>
    </section>

    <footer>
      <p>© <strong>MuteGuardian</strong> — Guruhingiz uchun ishonchli moderatsiya. Assalomu alaykum, botimizga xush kelibsiz!</p>
    </footer>
  </div>
</body>
</html>
