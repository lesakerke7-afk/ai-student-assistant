
import os
import json
import re
from datetime import date

import streamlit as st

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

# -------------------- БЕТТІҢ БАПТАУЛАРЫ --------------------
st.set_page_config(
    page_title="AI Student Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------- ДИЗАЙН --------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] {font-family: 'Inter', sans-serif;}
.stApp {
    background: radial-gradient(circle at 8% 0%, #e8edff 0, transparent 28%),
                linear-gradient(135deg, #f7f8ff 0%, #f3f6ff 55%, #eef7ff 100%);
}
.block-container {padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1180px;}
[data-testid="stSidebar"] {background: linear-gradient(180deg, #172554 0%, #312e81 100%);}
[data-testid="stSidebar"] * {color: #f8fafc !important;}
.hero {
    padding: 30px 32px; border-radius: 24px; color: white;
    background: linear-gradient(120deg, #312e81 0%, #4f46e5 52%, #0ea5e9 100%);
    box-shadow: 0 16px 40px rgba(49,46,129,.18); margin-bottom: 22px;
}
.hero h1 {font-size: 2.1rem; margin: 0 0 8px 0; font-weight: 800;}
.hero p {font-size: 1rem; opacity: .92; margin: 0;}
.eyebrow {font-size: .75rem; text-transform: uppercase; letter-spacing: .14em; opacity:.8; font-weight:700;}
.panel {
    background: rgba(255,255,255,.88); border: 1px solid #e5e7eb;
    border-radius: 18px; padding: 20px 22px; box-shadow: 0 8px 24px rgba(31,41,55,.05);
}
.small-muted {color:#64748b; font-size:.9rem;}
.metric {
    background:white; border:1px solid #e5e7eb; border-radius:16px;
    padding:18px; box-shadow:0 6px 18px rgba(31,41,55,.04);
}
.metric .number {font-size:1.8rem; font-weight:800; color:#3730a3;}
.metric .caption {color:#64748b; font-size:.86rem;}
div.stButton > button {
    border-radius: 12px; border: 0; font-weight: 700;
    background: linear-gradient(90deg,#4f46e5,#2563eb); color:white;
    padding:.62rem 1.1rem;
}
div.stButton > button:hover {color:white; border:0; filter:brightness(1.06);}
.stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
    border-radius: 12px !important;
}
div[data-testid="stChatMessage"] {border-radius: 16px; background:rgba(255,255,255,.8);}
footer {visibility:hidden;}
</style>
""", unsafe_allow_html=True)

# -------------------- API КІЛТІН ОҚУ --------------------
def get_api_key():
    try:
        key = st.secrets.get("GEMINI_API_KEY", "")
        if key:
            return key
    except Exception:
        pass
    return os.getenv("GEMINI_API_KEY", "")

def get_model_name():
    try:
        return st.secrets.get("GEMINI_MODEL", os.getenv("GEMINI_MODEL", "gemini-3.8-flash"))
    except Exception:
        return os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

def ask_ai(prompt, system_instruction="Сен студенттерге көмектесетін сыпайы, нақты әрі түсінікті қазақтілді оқу көмекшісісің."):
    """Gemini API арқылы жауап алады. API кілті болмаса, None қайтарады."""
    key = get_api_key()
    if not key or genai is None:
        return None
    try:
        client = genai.Client(api_key=key)
        response = client.models.generate_content(
            model=get_model_name(),
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.7,
                max_output_tokens=1200,
            ),
        )
        return (response.text or "").strip()
    except Exception as exc:
        # API қатесі интерфейсте түсінікті хабарлама ретінде көрсетіледі.
        return f"API_ERROR: {str(exc)[:350]}"

def init_state():
    defaults = {
        "chat_history": [],
        "quiz_data": None,
        "quiz_topic": "",
        "quiz_score": None,
        "completed_quizzes": 0,
        "total_points": 0,
        "planner_text": "",
        "student_name": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_state()

# -------------------- БҮЙІР МӘЗІР --------------------
with st.sidebar:
    st.markdown("## 🎓 AI Student")
    st.caption("Ақылды оқу көмекшісі")
    st.markdown("---")
    page = st.radio(
        "БӨЛІМДЕР",
        ["🏠 Басты бет", "🤖 AI Chat", "📚 Study Helper", "📝 AI Quiz", "📅 Study Planner", "🏆 My Progress"],
        label_visibility="visible",
    )
    st.markdown("---")
    st.markdown("**Студент профилі**")
    name = st.text_input("Есімің", value=st.session_state.student_name, placeholder="Мысалы: Акерке")
    st.session_state.student_name = name
    if get_api_key():
        st.success("Gemini AI қосылған")
    else:
        st.warning("Демо режимі: API кілті қосылмаған")
    st.caption("© 2026 AI Student Assistant")

def hero(title, subtitle, icon="✨"):
    st.markdown(
        f'<div class="hero"><div class="eyebrow">YOUR PERSONAL STUDY SPACE</div>'
        f'<h1>{icon} {title}</h1><p>{subtitle}</p></div>',
        unsafe_allow_html=True,
    )

def fallback_chat(question):
    q = question.lower()
    if any(word in q for word in ["сәлем", "салем", "hello"]):
        return "Сәлем! Мен AI Student Assistant көмекшісімін. Қандай оқу сұрағың бар?"
    if "python" in q:
        return "Python — үйренуге ыңғайлы бағдарламалау тілі. Ол айнымалылар, шартты операторлар, циклдер, функциялар және кітапханалар арқылы бағдарлама жасауға мүмкіндік береді."
    if "жасанды интеллект" in q or "ai" in q:
        return "Жасанды интеллект — компьютерлік жүйелердің мәтінді түсіну, ақпаратты талдау және ұсыныс жасау сияқты адам интеллектісіне тән міндеттерді орындау мүмкіндігі."
    if "алгоритм" in q:
        return "Алгоритм — белгілі бір мәселені шешуге арналған реттелген және нақты қадамдар жиынтығы. Негізгі қасиеттері: анықтылық, аяқталушылық, нәтижелілік және түсініктілік."
    if "оқу жоспары" in q or "жоспар" in q:
        return "Оқу жоспарын құру үшін: 1) міндеттерді тізімде; 2) маңыздылығына қарай ретте; 3) әр тапсырмаға уақыт белгіле; 4) қысқа үзілістер жоспарла; 5) күн соңында нәтижені тексер."
    return "Бұл демо режиміндегі үлгі жауап. Нақты AI жауабын алу үшін Gemini API кілтін қосу қажет. Әзірге сұрағыңды Python, алгоритм немесе жасанды интеллект тақырыбымен байланыстырып көр."

DEMO_QUIZ = [
    {
        "question": "Python тілінде экранға мәтін шығару үшін қай функция қолданылады?",
        "options": ["input()", "print()", "int()", "range()"],
        "answer": 1,
        "explanation": "print() функциясы экранға ақпарат шығарады."
    },
    {
        "question": "Алгоритм дегеніміз не?",
        "options": ["Компьютер құрылғысы", "Мәселені шешу қадамдарының реті", "Мәтіндік редактор", "Интернет желісі"],
        "answer": 1,
        "explanation": "Алгоритм — есепті шешуге арналған нақты қадамдар тізбегі."
    },
    {
        "question": "Python тілінде шартты оператордың негізгі кілт сөзі қайсы?",
        "options": ["if", "for", "def", "import"],
        "answer": 0,
        "explanation": "if шартының ақиқат/жалған болуына қарай код тармағын таңдайды."
    },
    {
        "question": "Жасанды интеллекттің бір қолданылу саласын көрсетіңіз.",
        "options": ["Тек қағаз басып шығару", "Мәтінді талдау", "Тек пернетақта теру", "Мониторды қосу"],
        "answer": 1,
        "explanation": "AI мәтінді талдау, аудару, сұрақтарға жауап беру сияқты міндеттерді орындай алады."
    },
    {
        "question": "Қай цикл белгілі бір шарт орындалып тұрған кезде қайталанады?",
        "options": ["while", "if", "return", "class"],
        "answer": 0,
        "explanation": "while циклі берілген шарт ақиқат болғанша қайталанады."
    },
]

def clean_json(text):
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text

def make_quiz(topic, count):
    prompt = f"""
    Қазақ тілінде "{topic}" тақырыбы бойынша дәл {count} тест сұрағын жаса.
    Тек JSON қайтар, Markdown қолданба.
    Формат:
    {{
      "questions": [
        {{
          "question": "Сұрақ мәтіні",
          "options": ["A нұсқа", "B нұсқа", "C нұсқа", "D нұсқа"],
          "answer": 0,
          "explanation": "Дұрыс жауаптың қысқаша түсіндірмесі"
        }}
      ]
    }}
    answer — дұрыс нұсқаның 0-ден басталатын индексі.
    Әр сұрақта 4 нұсқа болсын, бір ғана дұрыс жауап болсын.
    """
    result = ask_ai(prompt, "Сен сапалы оқу тесттерін құрастыратын көмекшісің. Дұрыс жауап индексін мұқият тексер.")
    if result and not result.startswith("API_ERROR:"):
        try:
            data = json.loads(clean_json(result))
            questions = data.get("questions", [])
            valid = []
            for item in questions:
                if (isinstance(item.get("question"), str)
                    and isinstance(item.get("options"), list)
                    and len(item["options"]) == 4
                    and isinstance(item.get("answer"), int)
                    and 0 <= item["answer"] < 4):
                    valid.append(item)
            if valid:
                return valid[:count], "AI"
        except Exception:
            pass
    # API жоқ/қате болса, сайт жұмысын көрсету үшін кіріктірілген демо тест қолданылады.
    return DEMO_QUIZ[:count], "Демо"

# -------------------- БАСТЫ БЕТ --------------------
if page == "🏠 Басты бет":
    first = f", {st.session_state.student_name}" if st.session_state.student_name else ""
    hero("Сәлем" + first + "!", "Оқуыңды жеңілдететін ақылды көмекші бір жерде.", "🎓")
    st.markdown("### Бүгін не істейміз?")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div class="metric"><div class="number">🤖</div><b>AI Chat</b><div class="caption">Сұрақ қойып, жауап ал</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="metric"><div class="number">📝</div><b>AI Quiz</b><div class="caption">Біліміңді тестпен тексер</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="metric"><div class="number">📅</div><b>Study Planner</b><div class="caption">Оқу жоспарын құрастыр</div></div>', unsafe_allow_html=True)
    st.write("")
    left, right = st.columns([1.35, 1])
    with left:
        st.markdown('<div class="panel"><h3>💡 Қалай қолдануға болады?</h3><ol><li>Сол жақ мәзірден қажетті бөлімді таңда.</li><li>Сұрағыңды немесе оқу тақырыбын енгіз.</li><li>AI жауабын оқып, тест арқылы біліміңді тексер.</li></ol></div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="panel"><h3>🚀 Жылдам бастау</h3><p class="small-muted">Мына сұрақтардың бірін AI Chat бөліміне енгізіп көр:</p><ul><li>Python дегеніміз не?</li><li>Алгоритмді түсіндір.</li><li>Жасанды интеллект қайда қолданылады?</li></ul></div>', unsafe_allow_html=True)
    st.info("Ескерту: Gemini API кілтін қоспасаң да, сайт демо режимінде ашылады. Нақты AI жауаптары үшін API кілті қажет.")

# -------------------- AI CHAT --------------------
elif page == "🤖 AI Chat":
    hero("AI Chat", "Оқу, бағдарламалау және технология туралы сұрақтарыңды қой.", "🤖")
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    prompt = st.chat_input("Мысалы: Python тіліндегі циклді түсіндір...")
    if prompt:
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Жауап дайындалып жатыр..."):
                if get_api_key():
                    transcript = "\n".join(
                        [f"{'Студент' if m['role']=='user' else 'Көмекші'}: {m['content']}"
                         for m in st.session_state.chat_history[-10:]]
                    )
                    answer = ask_ai(
                        "Мына диалогты жалғастыр. Қазақ тілінде нақты, түсінікті жауап бер:\n" + transcript
                    )
                    if not answer or answer.startswith("API_ERROR:"):
                        st.warning("AI сервисіне қосылу кезінде мәселе туындады. Демо жауап көрсетілді.")
                        answer = fallback_chat(prompt)
                else:
                    answer = fallback_chat(prompt)
                st.markdown(answer)
        st.session_state.chat_history.append({"role": "assistant", "content": answer})
    if st.button("🧹 Диалогты тазалау"):
        st.session_state.chat_history = []
        st.rerun()

# -------------------- STUDY HELPER --------------------
elif page == "📚 Study Helper":
    hero("Study Helper", "Тақырыпты түсін, мәтінді қысқарт немесе карточкалар жаса.", "📚")
    mode = st.selectbox("Көмек түрі", ["Тақырыпты түсіндіру", "Мәтінді қысқаша мазмұндау", "Терминдер мен флеш-карталар"])
    subject = st.text_input("Пән немесе тақырып", placeholder="Мысалы: Жасанды интеллект")
    material = st.text_area("Мәтін немесе сұрағың", height=180, placeholder="Осы жерге тақырыпты немесе мәтінді енгіз...")
    if st.button("✨ Орындау", key="study_action"):
        if not material.strip():
            st.warning("Алдымен мәтін немесе сұрақ енгіз.")
        else:
            prompts = {
                "Тақырыпты түсіндіру": "Тақырыпты студентке қарапайым тілмен түсіндір. Анықтама, негізгі ойлар және бір мысал келтір.",
                "Мәтінді қысқаша мазмұндау": "Берілген мәтінді негізгі мағынасын жоғалтпай, қазақ тілінде тармақтармен қысқаша мазмұнда.",
                "Терминдер мен флеш-карталар": "Мәтіннен 5 маңызды термин таңда. Әр терминге қысқа анықтама және сұрақ-жауап түріндегі флеш-карта жаса."
            }
            with st.spinner("Материал дайындалып жатыр..."):
                answer = ask_ai(f"Пән/тақырып: {subject}\nМатериал:\n{material}\n\nТапсырма: {prompts[mode]}")
                if not answer or answer.startswith("API_ERROR:"):
                    answer = "Бұл функция нақты AI режимінде жұмыс істеуі үшін Gemini API кілтін қосу қажет.\n\nДемо кеңес: тақырыпты анықтама, негізгі ерекшеліктер, қолданылу саласы және мысал бойынша бөліп оқы."
                st.markdown('<div class="panel">', unsafe_allow_html=True)
                st.markdown(answer)
                st.markdown('</div>', unsafe_allow_html=True)

# -------------------- AI QUIZ --------------------
elif page == "📝 AI Quiz":
    hero("AI Quiz", "Тақырыпты енгіз де, біліміңді тексеретін тест жаса.", "📝")
    topic = st.text_input("Тест тақырыбы", value=st.session_state.quiz_topic, placeholder="Мысалы: Python циклдері")
    count = st.slider("Сұрақ саны", min_value=3, max_value=5, value=5)
    if st.button("🎯 Тест құрастыру"):
        if not topic.strip():
            st.warning("Тест тақырыбын енгіз.")
        else:
            with st.spinner("Тест дайындалып жатыр..."):
                questions, source = make_quiz(topic, count)
                st.session_state.quiz_data = questions
                st.session_state.quiz_topic = topic
                st.session_state.quiz_score = None
                st.session_state.quiz_source = source
    if st.session_state.quiz_data:
        st.markdown(f"### {st.session_state.quiz_topic} бойынша тест")
        st.caption(f"Сұрақ көзі: {st.session_state.get('quiz_source', 'Демо')}")
        with st.form("quiz_form"):
            answers = []
            for i, q in enumerate(st.session_state.quiz_data):
                st.markdown(f"**{i+1}. {q['question']}**")
                choice = st.radio("Жауапты таңда", q["options"], key=f"quiz_{i}", index=None, label_visibility="collapsed")
                answers.append(choice)
            submitted = st.form_submit_button("Жауаптарды тексеру")
        if submitted:
            score = 0
            for q, chosen in zip(st.session_state.quiz_data, answers):
                if chosen is not None and chosen == q["options"][q["answer"]]:
                    score += 1
            st.session_state.quiz_score = score
            st.session_state.completed_quizzes += 1
            st.session_state.total_points += score
        if st.session_state.quiz_score is not None:
            score = st.session_state.quiz_score
            total = len(st.session_state.quiz_data)
            st.success(f"Нәтижең: {score}/{total} дұрыс жауап!")
            st.progress(score / total)
            for i, q in enumerate(st.session_state.quiz_data):
                correct = q["options"][q["answer"]]
                st.markdown(f"**{i+1}. Дұрыс жауап: {correct}**")
                st.caption(q.get("explanation", ""))
    else:
        st.markdown('<div class="panel"><b>🎓 Тест қалай жұмыс істейді?</b><p class="small-muted">AI қосылғанда тест тақырып бойынша автоматты жасалады. API кілті болмаса, Python және AI тақырыптарындағы демо тест көрсетіледі.</p></div>', unsafe_allow_html=True)

# -------------------- STUDY PLANNER --------------------
elif page == "📅 Study Planner":
    hero("Study Planner", "Уақытыңды тиімді жоспарла және тапсырмаларыңды ретте.", "📅")
    col1, col2 = st.columns(2)
    with col1:
        plan_date = st.date_input("Жоспар күні", value=date.today())
        subjects = st.text_area("Оқитын пәндер мен тапсырмалар", placeholder="Мысалы:\nPython – циклдерді қайталау\nПедагогика – лекция оқу\nАғылшын тілі – сөз жаттау", height=160)
    with col2:
        available = st.selectbox("Оқуға бөлетін уақыт", ["1 сағат", "2 сағат", "3 сағат", "4 сағат", "5 сағат немесе одан көп"])
        priority = st.selectbox("Басты басымдық", ["Емтиханға дайындық", "Үй тапсырмаларын орындау", "Жаңа тақырып оқу", "Жобамен жұмыс"])
    if st.button("📌 Жоспар құрастыру"):
        if not subjects.strip():
            st.warning("Кемінде бір пән немесе тапсырма енгіз.")
        else:
            with st.spinner("Жоспар жасалып жатыр..."):
                answer = ask_ai(
                    f"{plan_date} күніне студентке оқу жоспарын құрастыр. Уақыты: {available}. "
                    f"Басымдық: {priority}. Тапсырмалар: {subjects}. Үзілістерді де қос, жоспарды кесте түрінде бер."
                )
                if not answer or answer.startswith("API_ERROR:"):
                    lines = [x.strip(" -•") for x in subjects.splitlines() if x.strip()]
                    slots = ["09:00–09:30", "09:40–10:10", "10:20–10:50", "11:00–11:30", "11:40–12:10"]
                    answer = f"### {plan_date} күнгі демо оқу жоспары\n\n"
                    for i, item in enumerate(lines):
                        answer += f"- **{slots[i % len(slots)]}** — {item}\n"
                    answer += "\n- **Әр 30 минуттан кейін:** қысқа үзіліс жаса.\n- **Соңында:** орындалған тапсырмаларды белгіле."
                st.session_state.planner_text = answer
    if st.session_state.planner_text:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown(st.session_state.planner_text)
        st.markdown('</div>', unsafe_allow_html=True)

# -------------------- MY PROGRESS --------------------
elif page == "🏆 My Progress":
    hero("My Progress", "Оқу белсенділігің мен тест нәтижелерің.", "🏆")
    a, b, c = st.columns(3)
    with a:
        st.markdown(f'<div class="metric"><div class="number">{st.session_state.completed_quizzes}</div><div class="caption">Өткен тест саны</div></div>', unsafe_allow_html=True)
    with b:
        st.markdown(f'<div class="metric"><div class="number">{st.session_state.total_points}</div><div class="caption">Жиналған ұпай</div></div>', unsafe_allow_html=True)
    with c:
        st.markdown(f'<div class="metric"><div class="number">{len(st.session_state.chat_history)//2}</div><div class="caption">Чаттағы сұрақтар</div></div>', unsafe_allow_html=True)
    st.write("")
    st.info("Бұл көрсеткіштер осы браузер сессиясы кезінде сақталады. Бетті жаңадан ашқанда немесе сессия аяқталғанда бастапқы күйге оралуы мүмкін.")

st.markdown("---")
st.caption("AI Student Assistant — оқу мақсатындағы студенттік жоба. AI жауаптарын тексеріп қолдан.")
