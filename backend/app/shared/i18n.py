"""
Fixed document labels and dates in the document's language, so a Hindi (or any other) deliverable is
fully in that language — not just the AI-written body.
"""
import datetime
from typing import Dict

LABELS: Dict[str, Dict[str, str]] = {
    "English": {
        "document_control": "Document Control", "item": "Item", "detail": "Detail",
        "document_title": "Document Title", "file_name": "File Name", "version": "Version", "date": "Date",
        "authorship": "Authorship", "accessibility": "Accessibility",
        "authorship_text": "Prepared with ContentGenie (AI-generated, human-reviewed)",
        "accessibility_text": "Automated WCAG 2.2 AA checks: colour contrast, heading order, table headers",
        "prepared": "Prepared with ContentGenie", "presentation": "PRESENTATION", "slide": "SLIDE", "by": "By ContentGenie",
    },
    "Hindi": {
        "document_control": "दस्तावेज़ नियंत्रण", "item": "मद", "detail": "विवरण",
        "document_title": "दस्तावेज़ का शीर्षक", "file_name": "फ़ाइल का नाम", "version": "संस्करण", "date": "दिनांक",
        "authorship": "लेखन", "accessibility": "सुगम्यता",
        "authorship_text": "ContentGenie द्वारा तैयार (AI-जनित, मानव-समीक्षित)",
        "accessibility_text": "स्वचालित WCAG 2.2 AA जाँच: रंग कंट्रास्ट, शीर्षक क्रम, तालिका शीर्षक",
        "prepared": "ContentGenie द्वारा तैयार", "presentation": "प्रस्तुति", "slide": "स्लाइड", "by": "ContentGenie द्वारा",
    },
    "Marathi": {
        "document_control": "दस्तऐवज नियंत्रण", "item": "बाब", "detail": "तपशील",
        "document_title": "दस्तऐवजाचे शीर्षक", "file_name": "फाइलचे नाव", "version": "आवृत्ती", "date": "दिनांक",
        "authorship": "लेखन", "accessibility": "सुलभता",
        "authorship_text": "ContentGenie द्वारे तयार (AI-निर्मित, मानवाने पुनरावलोकन केलेले)",
        "accessibility_text": "स्वयंचलित WCAG 2.2 AA तपासणी: रंग कॉन्ट्रास्ट, शीर्षक क्रम, तक्त्याची शीर्षके",
        "prepared": "ContentGenie द्वारे तयार", "presentation": "सादरीकरण", "slide": "स्लाइड", "by": "ContentGenie द्वारे",
    },
    "Tamil": {
        "document_control": "ஆவணக் கட்டுப்பாடு", "item": "உருப்படி", "detail": "விவரம்",
        "document_title": "ஆவணத் தலைப்பு", "file_name": "கோப்பின் பெயர்", "version": "பதிப்பு", "date": "தேதி",
        "authorship": "ஆக்கம்", "accessibility": "அணுகல்தன்மை",
        "authorship_text": "ContentGenie மூலம் தயாரிக்கப்பட்டது (AI உருவாக்கியது, மனிதரால் சரிபார்க்கப்பட்டது)",
        "accessibility_text": "தானியங்கி WCAG 2.2 AA சோதனைகள்: வண்ண வேறுபாடு, தலைப்பு வரிசை, அட்டவணைத் தலைப்புகள்",
        "prepared": "ContentGenie மூலம் தயாரிக்கப்பட்டது", "presentation": "விளக்கக்காட்சி", "slide": "ஸ்லைடு", "by": "ContentGenie மூலம்",
    },
    "Telugu": {
        "document_control": "పత్ర నియంత్రణ", "item": "అంశం", "detail": "వివరాలు",
        "document_title": "పత్రం శీర్షిక", "file_name": "ఫైల్ పేరు", "version": "సంస్కరణ", "date": "తేదీ",
        "authorship": "రచన", "accessibility": "అందుబాటు",
        "authorship_text": "ContentGenie ద్వారా తయారుచేయబడింది (AI రూపొందించినది, మానవులు సమీక్షించినది)",
        "accessibility_text": "స్వయంచాలక WCAG 2.2 AA తనిఖీలు: రంగు కాంట్రాస్ట్, శీర్షికల క్రమం, పట్టిక శీర్షికలు",
        "prepared": "ContentGenie ద్వారా తయారుచేయబడింది", "presentation": "ప్రజెంటేషన్", "slide": "స్లయిడ్", "by": "ContentGenie ద్వారా",
    },
    "Bengali": {
        "document_control": "নথি নিয়ন্ত্রণ", "item": "বিষয়", "detail": "বিবরণ",
        "document_title": "নথির শিরোনাম", "file_name": "ফাইলের নাম", "version": "সংস্করণ", "date": "তারিখ",
        "authorship": "রচনা", "accessibility": "প্রবেশযোগ্যতা",
        "authorship_text": "ContentGenie দ্বারা প্রস্তুত (AI-নির্মিত, মানুষের দ্বারা পর্যালোচিত)",
        "accessibility_text": "স্বয়ংক্রিয় WCAG 2.2 AA পরীক্ষা: রঙের কনট্রাস্ট, শিরোনামের ক্রম, সারণির শিরোনাম",
        "prepared": "ContentGenie দ্বারা প্রস্তুত", "presentation": "উপস্থাপনা", "slide": "স্লাইড", "by": "ContentGenie দ্বারা",
    },
    "Gujarati": {
        "document_control": "દસ્તાવેજ નિયંત્રણ", "item": "બાબત", "detail": "વિગત",
        "document_title": "દસ્તાવેજનું શીર્ષક", "file_name": "ફાઇલનું નામ", "version": "આવૃત્તિ", "date": "તારીખ",
        "authorship": "લેખન", "accessibility": "સુલભતા",
        "authorship_text": "ContentGenie દ્વારા તૈયાર (AI-નિર્મિત, માનવ દ્વારા સમીક્ષિત)",
        "accessibility_text": "સ્વચાલિત WCAG 2.2 AA તપાસ: રંગ કોન્ટ્રાસ્ટ, શીર્ષક ક્રમ, કોષ્ટક શીર્ષકો",
        "prepared": "ContentGenie દ્વારા તૈયાર", "presentation": "પ્રસ્તુતિ", "slide": "સ્લાઇડ", "by": "ContentGenie દ્વારા",
    },
    "Kannada": {
        "document_control": "ದಾಖಲೆ ನಿಯಂತ್ರಣ", "item": "ಅಂಶ", "detail": "ವಿವರ",
        "document_title": "ದಾಖಲೆಯ ಶೀರ್ಷಿಕೆ", "file_name": "ಫೈಲ್ ಹೆಸರು", "version": "ಆವೃತ್ತಿ", "date": "ದಿನಾಂಕ",
        "authorship": "ರಚನೆ", "accessibility": "ಪ್ರವೇಶಸಾಧ್ಯತೆ",
        "authorship_text": "ContentGenie ಮೂಲಕ ಸಿದ್ಧಪಡಿಸಲಾಗಿದೆ (AI-ರಚಿತ, ಮಾನವರಿಂದ ಪರಿಶೀಲಿತ)",
        "accessibility_text": "ಸ್ವಯಂಚಾಲಿತ WCAG 2.2 AA ಪರಿಶೀಲನೆಗಳು: ಬಣ್ಣದ ಕಾಂಟ್ರಾಸ್ಟ್, ಶೀರ್ಷಿಕೆ ಕ್ರಮ, ಕೋಷ್ಟಕ ಶೀರ್ಷಿಕೆಗಳು",
        "prepared": "ContentGenie ಮೂಲಕ ಸಿದ್ಧಪಡಿಸಲಾಗಿದೆ", "presentation": "ಪ್ರಸ್ತುತಿ", "slide": "ಸ್ಲೈಡ್", "by": "ContentGenie ಮೂಲಕ",
    },
    "Spanish": {
        "document_control": "Control del documento", "item": "Elemento", "detail": "Detalle",
        "document_title": "Título del documento", "file_name": "Nombre del archivo", "version": "Versión", "date": "Fecha",
        "authorship": "Autoría", "accessibility": "Accesibilidad",
        "authorship_text": "Elaborado con ContentGenie (generado por IA, revisado por personas)",
        "accessibility_text": "Comprobaciones automáticas WCAG 2.2 AA: contraste de color, orden de encabezados, encabezados de tabla",
        "prepared": "Elaborado con ContentGenie", "presentation": "PRESENTACIÓN", "slide": "DIAPOSITIVA", "by": "Por ContentGenie",
    },
    "French": {
        "document_control": "Contrôle du document", "item": "Élément", "detail": "Détail",
        "document_title": "Titre du document", "file_name": "Nom du fichier", "version": "Version", "date": "Date",
        "authorship": "Rédaction", "accessibility": "Accessibilité",
        "authorship_text": "Préparé avec ContentGenie (généré par IA, relu par un humain)",
        "accessibility_text": "Contrôles automatiques WCAG 2.2 AA : contraste des couleurs, ordre des titres, en-têtes de tableau",
        "prepared": "Préparé avec ContentGenie", "presentation": "PRÉSENTATION", "slide": "DIAPOSITIVE", "by": "Par ContentGenie",
    },
    "German": {
        "document_control": "Dokumentenkontrolle", "item": "Punkt", "detail": "Angabe",
        "document_title": "Dokumenttitel", "file_name": "Dateiname", "version": "Version", "date": "Datum",
        "authorship": "Urheberschaft", "accessibility": "Barrierefreiheit",
        "authorship_text": "Erstellt mit ContentGenie (KI-generiert, von Menschen geprüft)",
        "accessibility_text": "Automatisierte WCAG 2.2 AA-Prüfungen: Farbkontrast, Überschriftenreihenfolge, Tabellenüberschriften",
        "prepared": "Erstellt mit ContentGenie", "presentation": "PRÄSENTATION", "slide": "FOLIE", "by": "Von ContentGenie",
    },
}

MONTHS: Dict[str, list] = {
    "English": "January February March April May June July August September October November December".split(),
    "Hindi": "जनवरी फ़रवरी मार्च अप्रैल मई जून जुलाई अगस्त सितंबर अक्टूबर नवंबर दिसंबर".split(),
    "Marathi": "जानेवारी फेब्रुवारी मार्च एप्रिल मे जून जुलै ऑगस्ट सप्टेंबर ऑक्टोबर नोव्हेंबर डिसेंबर".split(),
    "Tamil": "ஜனவரி பிப்ரவரி மார்ச் ஏப்ரல் மே ஜூன் ஜூலை ஆகஸ்ட் செப்டம்பர் அக்டோபர் நவம்பர் டிசம்பர்".split(),
    "Telugu": "జనవరి ఫిబ్రవరి మార్చి ఏప్రిల్ మే జూన్ జూలై ఆగస్టు సెప్టెంబర్ అక్టోబర్ నవంబర్ డిసెంబర్".split(),
    "Bengali": "জানুয়ারি ফেব্রুয়ারি মার্চ এপ্রিল মে জুন জুলাই আগস্ট সেপ্টেম্বর অক্টোবর নভেম্বর ডিসেম্বর".split(),
    "Gujarati": "જાન્યુઆરી ફેબ્રુઆરી માર્ચ એપ્રિલ મે જૂન જુલાઈ ઑગસ્ટ સપ્ટેમ્બર ઑક્ટોબર નવેમ્બર ડિસેમ્બર".split(),
    "Kannada": "ಜನವರಿ ಫೆಬ್ರವರಿ ಮಾರ್ಚ್ ಏಪ್ರಿಲ್ ಮೇ ಜೂನ್ ಜುಲೈ ಆಗಸ್ಟ್ ಸೆಪ್ಟೆಂಬರ್ ಅಕ್ಟೋಬರ್ ನವೆಂಬರ್ ಡಿಸೆಂಬರ್".split(),
    "Spanish": "enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre".split(),
    "French": "janvier février mars avril mai juin juillet août septembre octobre novembre décembre".split(),
    "German": "Januar Februar März April Mai Juni Juli August September Oktober November Dezember".split(),
}


def labels(language: str) -> Dict[str, str]:
    return LABELS.get(language or "English", LABELS["English"])


def format_date(language: str, day: datetime.date = None) -> str:
    day = day or datetime.date.today()
    months = MONTHS.get(language or "English", MONTHS["English"])
    return f"{day.day:02d} {months[day.month - 1]} {day.year}"


SMALL_WORDS = {"a", "an", "and", "as", "at", "but", "by", "for", "in", "of", "on", "or", "the", "to", "vs", "with"}


def smart_title(title: str) -> str:
    """Capitalise an all-lowercase English title ('importance of diet' -> 'Importance of Diet'); leave others as typed."""
    if not title or title != title.lower() or not any(c.isascii() and c.isalpha() for c in title):
        return title
    words = title.split()
    return " ".join(w if (i and w in SMALL_WORDS) else w[:1].upper() + w[1:] for i, w in enumerate(words))
