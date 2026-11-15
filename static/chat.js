// Chat page logic. Nothing typed here is stored in the browser either.
(function () {
  const CSRF = document.querySelector('meta[name="csrf-token"]').content;
  const log = document.getElementById("log");
  const menu = document.getElementById("menu");
  const composer = document.getElementById("composer");
  const input = document.getElementById("msg");
  const booking = document.getElementById("booking");
  const crisis = document.getElementById("crisis");
  const bookingErr = document.getElementById("booking-error");
  let lang = "ar";

  const T = {
    ar: { typing: "المساعد بيكتب…", helpful: "الرد ده مفيد؟", yes: "نعم", no: "لا", thanks: "شكرًا على رأيك 🙏",
          bookNow: "📅 احجز جلسة", err: { day: "اختار اليوم", time: "اختار الوقت", method: "اختار طريقة التواصل",
          contact: "اكتب رقم موبايل مصري صحيح (01xxxxxxxxx) أو إيميل صحيح", limit: "وصلت للحد الأقصى للحجوزات من الجلسة دي – كلّم الوحدة مباشرة",
          busy: "ملف الحجوزات مشغول حاليًا، جرّب كمان دقيقة أو كلّم الوحدة", net: "حصلت مشكلة في الاتصال، جرّب تاني" },
          closed: "تمام، أنا هنا لو احتجت حاجة. ولو رجعت حسيت بخطر، الأرقام في الشريط الأحمر فوق." },
    en: { typing: "Assistant is typing…", helpful: "Was this helpful?", yes: "Yes", no: "No", thanks: "Thanks for your feedback 🙏",
          bookNow: "📅 Book a session", err: { day: "Choose a day", time: "Choose a time", method: "Choose a contact method",
          contact: "Enter a valid Egyptian mobile (01xxxxxxxxx) or email", limit: "Booking limit reached for this session – please call the unit",
          busy: "The bookings file is busy, try again in a minute", net: "Connection problem, please try again" },
          closed: "Okay, I'm here if you need anything. If you feel unsafe again, the numbers are in the red banner." },
  };

  function add(who, html, opts = {}) {
    const row = document.createElement("div");
    row.className = "msg " + who;
    const b = document.createElement("div");
    b.className = "bubble";
    if (who === "user") b.textContent = html; else b.innerHTML = html;
    row.appendChild(b);
    log.appendChild(row);
    if (opts.feedback) addFeedback(b);
    if (opts.bookButton) {
      const btn = document.createElement("button");
      btn.className = "btn ghost small"; btn.type = "button"; btn.textContent = T[lang].bookNow;
      btn.style.marginTop = ".5rem";
      btn.onclick = () => send({ action: "booking" }, T[lang].bookNow);
      b.appendChild(document.createElement("br")); b.appendChild(btn);
    }
    log.scrollTop = log.scrollHeight;
    return b;
  }

  function addFeedback(bubble) {
    const fb = document.createElement("div");
    fb.className = "fb";
    fb.innerHTML = `<span>${T[lang].helpful}</span>`;
    ["yes", "no"].forEach((v) => {
      const btn = document.createElement("button");
      btn.type = "button"; btn.textContent = T[lang][v];
      btn.onclick = async () => {
        fb.textContent = T[lang].thanks;
        await post("/api/feedback", { helpful: v }).catch(() => {});
      };
      fb.appendChild(btn);
    });
    bubble.appendChild(fb);
  }

  async function post(url, body) {
    const r = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRF-Token": CSRF },
      body: JSON.stringify(body),
    });
    const data = await r.json().catch(() => ({}));
    return { ok: r.ok, data };
  }

  function showCrisis(data) {
    crisis.hidden = false;
    booking.hidden = true;
    menu.classList.add("disabled");
    document.getElementById("crisis-text").innerHTML = data.html;
    const ul = document.getElementById("crisis-contacts");
    ul.innerHTML = "";
    (data.contacts || []).forEach((c) => {
      const li = document.createElement("li");
      const a = document.createElement("a");
      a.href = c.href;
      a.innerHTML = `<span></span><b dir="ltr"></b>`;
      a.querySelector("span").textContent = c.label;
      a.querySelector("b").textContent = c.value;
      li.appendChild(a); ul.appendChild(li);
    });
    crisis.scrollIntoView({ behavior: "smooth", block: "center" });
    crisis.querySelector("a.btn").focus({ preventScroll: true });
  }

  async function send(payload, shownText) {
    if (shownText) add("user", shownText);
    const typing = add("bot", `<span class="typing">${T[lang].typing}</span>`);
    let res;
    try { res = await post("/api/chat", payload); }
    catch (e) { typing.parentElement.remove(); add("bot", T[lang].err.net); return; }
    typing.parentElement.remove();
    const d = res.data;
    lang = d.lang || lang;
    if (d.type === "crisis") {
      showCrisis(d);
      return;
    }
    add("bot", d.html, { feedback: d.type === "answer", bookButton: d.offer_booking });
    if (d.type === "booking") openBooking();
  }

  function openBooking() {
    booking.hidden = false;
    bookingErr.hidden = true;
    booking.scrollIntoView({ behavior: "smooth", block: "nearest" });
    booking.querySelector("input").focus({ preventScroll: true });
  }

  // contact field adapts to method
  booking.addEventListener("change", (e) => {
    if (e.target.name !== "method") return;
    const c = document.getElementById("contact");
    const isMail = e.target.value === "email";
    c.type = isMail ? "email" : "tel";
    c.placeholder = isMail ? "name@example.com" : "01xxxxxxxxx";
    c.inputMode = isMail ? "email" : "tel";
  });

  booking.addEventListener("submit", async (e) => {
    e.preventDefault();
    const f = new FormData(booking);
    const body = Object.fromEntries(f.entries());
    let res;
    try { res = await post("/api/book", body); }
    catch (err) { bookingErr.textContent = T[lang].err.net; bookingErr.hidden = false; return; }
    if (!res.ok || !res.data.ok) {
      const errs = (res.data.errors || ["net"]).map((k) => T[lang].err[k] || k);
      bookingErr.textContent = errs.join(" · ");
      bookingErr.hidden = false;
      return;
    }
    booking.reset();
    booking.hidden = true;
    add("bot", res.data.html);
  });

  document.getElementById("booking-cancel").onclick = () => (booking.hidden = true);
  document.getElementById("crisis-book").onclick = () => { openBooking(); };
  document.getElementById("crisis-close").onclick = async () => {
    await post("/api/crisis/close", {}).catch(() => {});
    crisis.hidden = true;
    menu.classList.remove("disabled");
    add("bot", T[lang].closed);
  };

  menu.addEventListener("click", (e) => {
    const b = e.target.closest("button[data-action]");
    if (!b) return;
    send({ action: b.dataset.action }, b.textContent.trim());
  });

  composer.addEventListener("submit", (e) => {
    e.preventDefault();
    const text = input.value.trim();
    if (!text) return;
    input.value = "";
    send({ message: text }, text);
  });

  if (window.START_IN_CRISIS) send({ action: "crisis" });
})();
