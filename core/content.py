"""Approved content shown by the assistant.

RULE: the assistant only shows text from this file. It never generates
advice, never diagnoses and never gives treatment advice.
STATUS: every text below is a DRAFT written by the student team and must be
reviewed and approved by the unit's specialists before any pilot.
"""
from config import NATIONAL_HOTLINE, UNIT

APPROVAL_STATUS = "DRAFT – pending approval by the counselling unit's specialists"

INTRO = {
    "ar": ("أهلًا بيك 👋 أنا <b>مساعد آلي</b> (برنامج كمبيوتر، مش إنسان) تابع لوحدة الإرشاد. "
           "أقدر أعرّفك بخدمات الوحدة، وأحجزلك جلسة من غير ما أسألك عن اسمك، وأوريك مقالات توعية. "
           "<br>أنا مش معالج ومش بقدّم تشخيص. لو محتاج تتكلم مع إنسان دلوقتي، استخدم الشريط الأحمر فوق."),
    "en": ("Hi 👋 I'm an <b>automated assistant</b> (a computer program, not a person) for the counselling unit. "
           "I can explain the unit's services, book a session without asking your name, and show awareness articles. "
           "<br>I'm not a therapist and I don't diagnose. To talk to a person now, use the red banner at the top."),
}

RESPONSES = {
    "services": {
        "ar": (f"<b>خدمات {UNIT['name_ar']}:</b><ul>"
               "<li>جلسات إرشاد نفسي فردية – <b>مجانية وسرية</b></li>"
               "<li>إرشاد أكاديمي: تنظيم الوقت، مهارات المذاكرة، اختيار القسم</li>"
               "<li>ورش وندوات توعية وجلسات دعم جماعي</li>"
               "<li>توجيه لجهات متخصصة لو احتاج الأمر</li></ul>"
               f"📍 {UNIT['location_ar']}<br>🕘 {UNIT['hours_ar']}<br>"
               f"☎️ {UNIT['phone']} – ✉️ {UNIT['email']}<br>"
               "الأخصائيين مش بيكتبوا أدوية، وما بيتكلموش عن جلستك مع أي حد إلا في حالة خطر على حياتك أو حياة غيرك."),
        "en": ("<b>Our services:</b><ul>"
               "<li>Individual counselling sessions – <b>free and confidential</b></li>"
               "<li>Academic guidance: time management, study skills, choosing a department</li>"
               "<li>Awareness workshops and group support sessions</li>"
               "<li>Referral to specialised services when needed</li></ul>"
               f"📍 {UNIT['location_en']}<br>🕘 {UNIT['hours_en']}<br>"
               f"☎️ {UNIT['phone']} – ✉️ {UNIT['email']}<br>"
               "Counsellors do not prescribe medication, and they keep what you say private unless "
               "someone's life is in danger."),
    },
    "stress": {
        "ar": ("واضح إن الفترة دي فيها ضغط عليك، وده شعور طبيعي وكتير من الطلبة بيمرّوا بيه. 💙<br>"
               "كتبت الوحدة مقالات قصيرة ممكن تفيدك: "
               "<a href='/awareness/exam-stress'>ضغط الامتحانات</a> · "
               "<a href='/awareness/sleep-and-study'>النوم والمذاكرة</a> · "
               "<a href='/awareness/time-management'>تنظيم الوقت</a><br>"
               "ولو حابب تتكلم مع أخصائي، أقدر أحجزلك جلسة دلوقتي."),
        "en": ("It sounds like you're under pressure right now — that's common and many students feel it. 💙<br>"
               "The unit wrote short articles that may help: "
               "<a href='/awareness/exam-stress'>Exam stress</a> · "
               "<a href='/awareness/sleep-and-study'>Sleep & study</a> · "
               "<a href='/awareness/time-management'>Time management</a><br>"
               "If you'd like to talk to a counsellor, I can book a session for you now."),
    },
    "booking": {
        "ar": "تمام 👍 اختار اليوم والوقت وطريقة التواصل في الفورم اللي تحت. <b>مش هنسألك عن اسمك.</b>",
        "en": "Sure 👍 choose a day, a time and how we should contact you below. <b>We won't ask for your name.</b>",
    },
    "other": {
        "ar": "أنا مساعد وحدة الإرشاد بس، فممكن ما أعرفش أرد على ده. اختار من القائمة أو اكتبلي محتاج إيه من الوحدة.",
        "en": "I'm only the counselling unit's assistant, so I may not be able to help with that. "
              "Please pick an option below or tell me what you need from the unit.",
    },
    "unsure": {
        "ar": "مش متأكد إني فهمتك صح 🙏 تحب تختار من القائمة؟",
        "en": "I'm not sure I understood 🙏 Would you like to choose from the menu?",
    },
}

CRISIS = {
    "ar": ("<b>شكرًا إنك قلت كده. اللي إنت حاسس بيه مهم، وإنت مش لوحدك.</b><br>"
           "أنا برنامج ومش هقدر أساعدك في ده لوحدي، لكن فيه ناس حقيقيين جاهزين يسمعوك <b>دلوقتي</b>:"),
    "en": ("<b>Thank you for telling me. What you're feeling matters, and you are not alone.</b><br>"
           "I'm a program and can't help with this on my own, but real people are ready to listen <b>right now</b>:"),
}

CRISIS_CONTACTS = [
    {"label_ar": "الخط الساخن للصحة النفسية (مجاني، 24 ساعة)", "label_en": "National mental-health hotline",
     "value": NATIONAL_HOTLINE, "href": f"tel:{NATIONAL_HOTLINE}"},
    {"label_ar": "تليفون وحدة الإرشاد", "label_en": "Counselling unit phone",
     "value": UNIT["phone"], "href": f"tel:{UNIT['phone']}"},
    {"label_ar": "واتساب الوحدة", "label_en": "Unit WhatsApp",
     "value": UNIT["whatsapp"], "href": f"https://wa.me/2{UNIT['whatsapp']}"},
    {"label_ar": "الإسعاف (لو في خطر فوري)", "label_en": "Ambulance (immediate danger)",
     "value": "123", "href": "tel:123"},
]

AWARENESS = [
    {"slug": "what-is-counselling", "icon": "🤝",
     "title": "يعني إيه إرشاد نفسي؟ وليه مش عيب",
     "summary": "الإرشاد مش للناس اللي عندها مشكلة كبيرة بس — هو مساحة آمنة تتكلم فيها.",
     "body": [
         "الإرشاد النفسي هو مقابلة سرية مع أخصائي بيساعدك تفهم اللي بتمر بيه وتلاقي طرق تتعامل بيها معاه.",
         "زيارة الوحدة مش معناها إن فيك حاجة غلط. طلبة كتير بييجوا عشان ضغط الدراسة، أو الغربة، أو مشاكل مع الأهل أو الأصحاب، أو عشان محتارين في اختيار القسم.",
         "الجلسات مجانية، وما حدش من الدكاترة أو أهلك بيعرف إنك جيت. الاستثناء الوحيد هو لو فيه خطر على حياتك أو حياة حد تاني.",
         "أول جلسة غالبًا بتكون تعارف: الأخصائي بيسمعك، وإنت اللي بتقرر تتكلم في إيه.",
     ]},
    {"slug": "exam-stress", "icon": "📚",
     "title": "ضغط الامتحانات",
     "summary": "شوية قلق قبل الامتحان طبيعي وبيساعدك تركز. المهم ما يزيدش عن حده.",
     "body": [
         "التوتر قبل الامتحان رد فعل طبيعي من الجسم، وبدرجة بسيطة بيزوّد تركيزك.",
         "قسّم المذاكرة لأجزاء صغيرة بأهداف واضحة، وخد راحة قصيرة كل 45–50 دقيقة.",
         "النوم الكويس ليلة الامتحان أهم من السهر لآخر لحظة؛ المخ بيثبّت المعلومات وإنت نايم.",
         "لو حسيت بتوتر جامد: خد نفس بطيء من مناخيرك 4 ثواني، اكتمه ثانيتين، وطلّعه 6 ثواني، وكرر كذا مرة.",
         "لو القلق مأثر على نومك أو أكلك أو حياتك اليومية لفترة طويلة، كلم الوحدة واحجز جلسة.",
     ]},
    {"slug": "sleep-and-study", "icon": "🌙",
     "title": "النوم والمذاكرة",
     "summary": "النوم مش وقت ضايع — هو جزء من المذاكرة.",
     "body": [
         "حاول تنام وتصحى في مواعيد ثابتة على قد ما تقدر، حتى في الإجازة.",
         "قلل الموبايل والشاشات قبل النوم بنص ساعة.",
         "قلل القهوة والمشروبات اللي فيها كافيين بعد العصر.",
         "لو فضلت مش عارف تنام أكتر من أسبوعين، اتكلم مع أخصائي في الوحدة.",
     ]},
    {"slug": "time-management", "icon": "⏰",
     "title": "تنظيم الوقت والتأجيل",
     "summary": "التأجيل مش كسل — غالبًا هو هروب من مهمة حاسسها كبيرة أو صعبة.",
     "body": [
         "اكتب كل المطلوب منك في ورقة واحدة، ورتبه حسب الأهمية والميعاد.",
         "ابدأ بأصغر خطوة ممكنة: «هفتح الملف وأقرا أول صفحة» أسهل من «هذاكر المادة».",
         "جرب طريقة 25 دقيقة شغل و5 دقايق راحة.",
         "الوحدة بتعمل ورش عن تنظيم الوقت؛ اسأل عن ميعاد الورشة الجاية.",
     ]},
    {"slug": "helping-a-friend", "icon": "🫂",
     "title": "صاحبك مش كويس؟ تعمل إيه",
     "summary": "مش مطلوب منك تحل المشكلة — المطلوب تسمع وتوصّله لحد متخصص.",
     "body": [
         "اسمعه من غير ما تحكم عليه أو تقلل من اللي هو حاسس بيه.",
         "لو قال كلام عن إنه عايز يموت أو يأذي نفسه، خد الكلام بجدية ومتوعدوش إنك هتخبي ده.",
         "شجّعه يكلم الوحدة أو الخط الساخن 16328، وممكن تعرض تروح معاه.",
         "لو في خطر فوري، اتصل بالإسعاف 123 وما تسيبوش لوحده.",
         "اهتم بنفسك كمان؛ إنك تساند حد ده بيتعب، ومن حقك تطلب دعم إنت كمان.",
     ]},
]


def awareness_by_slug(slug):
    return next((a for a in AWARENESS if a["slug"] == slug), None)
