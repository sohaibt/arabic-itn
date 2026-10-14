import json
import os
import subprocess
import sys
import unittest

from arabic_itn import normalize

HERE = os.path.dirname(os.path.abspath(__file__))


def t(s, **kw):
    return normalize(s, **kw)["text"]


class Numbers(unittest.TestCase):
    def test_eastern_digits(self):
        self.assertEqual(t("المبلغ ٢٥٠"), "المبلغ 250")
        self.assertEqual(t("عندي ٣ أولاد"), "عندي 3 أولاد")
        self.assertEqual(t("۱۲۳۴"), "1234")

    def test_compound_words(self):
        self.assertEqual(t("عمري خمسة وعشرين سنة"), "عمري 25 سنة")
        self.assertEqual(t("ميتين وخمسين"), "250")
        self.assertEqual(t("ثلاثمائة وخمسة وستون"), "365")
        self.assertEqual(t("ألف وتسعمية وتسعين"), "1990")
        self.assertEqual(t("ألفين وستة وعشرين"), "2026")
        self.assertEqual(t("خمسة عشر"), "15")
        self.assertEqual(t("خمستاشر"), "15")
        self.assertEqual(t("تلات مية"), "300")
        self.assertEqual(t("تلاتة آلاف وخمسمية"), "3500")
        self.assertEqual(t("عشرين ألف"), "20000")
        self.assertEqual(t("مية وخمسة وعشرين ألف"), "125000")
        self.assertEqual(t("اتنين مليون"), "2000000")
        self.assertEqual(t("خمسة و عشرين"), "25")

    def test_small_single_words_kept(self):
        self.assertEqual(t("واحد صاحبي"), "واحد صاحبي")
        self.assertEqual(t("عندي ثلاث أولاد"), "عندي ثلاث أولاد")
        self.assertEqual(t("ألف مبروك"), "ألف مبروك")
        self.assertEqual(t("خمسة ستة أيام"), "خمسة ستة أيام")

    def test_spans(self):
        r = normalize("عمري خمسة وعشرين سنة")
        self.assertEqual(r["spans"], [{"type": "number", "raw": "خمسة وعشرين", "value": "25"}])

    def test_conjunction_prefix_kept(self):
        self.assertEqual(t("كتاب وخمسة وعشرين قلم"), "كتاب و25 قلم")


class Phones(unittest.TestCase):
    def test_digit_by_digit_saudi(self):
        self.assertEqual(t("رقمي صفر خمسة صفر واحد اتنين تلاتة اربعة خمسة ستة سبعة"), "رقمي +966501234567")

    def test_eastern_digits_phone(self):
        self.assertEqual(t("رقمي ٠٥٠١٢٣٤٥٦٧"), "رقمي +966501234567")

    def test_uae_default_country(self):
        self.assertEqual(t("صفر خمسة صفر واحد اتنين تلاتة اربعة خمسة ستة سبعة", country="AE"), "+971501234567")

    def test_grouped_speech(self):
        self.assertEqual(t("صفر خمسة خمسة، مية وتلاتة وعشرين، خمسة وأربعين، سبعة وستين"), "+966551234567")

    def test_double_and_triple(self):
        self.assertEqual(t("صفر خمسة دبل خمسة واحد اتنين تريبل تلاتة ستة"), "+966555123336")
        self.assertEqual(t("zero five double five واحد اتنين تلاتة اربعة خمسة ستة"), "zero five double five 123456")

    def test_international_prefix(self):
        self.assertEqual(t("زائد تسعة سبعة واحد خمسة صفر واحد اتنين تلاتة اربعة خمسة ستة سبعة"), "+971501234567")
        self.assertEqual(t("صفر صفر تسعة ستة ستة خمسة خمسة واحد اتنين تلاتة اربعة خمسة ستة سبعة"), "+966551234567")
        self.assertEqual(t("+966 50 123 4567"), "+966501234567")
        self.assertEqual(t("971-50-123-4567"), "+971501234567")

    def test_punctuated_groups(self):
        self.assertEqual(t("الرقم صفر خمسة خمسة، واحد اتنين تلاتة، اربعة خمسة ستة سبعة."), "الرقم +966551234567.")

    def test_digit_runs(self):
        self.assertEqual(t("الكود واحد اتنين تلاتة اربعة"), "الكود 1234")
        self.assertEqual(t("خمسة ستة أيام"), "خمسة ستة أيام")

    def test_phone_span(self):
        r = normalize("رقمي صفر خمسة صفر واحد اتنين تلاتة اربعة خمسة ستة سبعة")
        self.assertEqual(r["spans"][0]["type"], "phone")
        self.assertEqual(r["spans"][0]["value"], "+966501234567")


class Money(unittest.TestCase):
    def test_currencies(self):
        self.assertEqual(t("المبلغ ميتين وخمسين ريال"), "المبلغ 250 SAR")
        self.assertEqual(t("خمسين درهم"), "50 AED")
        self.assertEqual(t("مية جنيه مصري"), "100 EGP")
        self.assertEqual(t("عشرين دولار"), "20 USD")
        self.assertEqual(t("ألف ريال سعودي"), "1000 SAR")
        self.assertEqual(t("خمسة آلاف درهم إماراتي"), "5000 AED")
        self.assertEqual(t("٢٥٠ ريال"), "250 SAR")
        self.assertEqual(t("ثلاثة ريالات"), "3 SAR")

    def test_subunits(self):
        self.assertEqual(t("عشرة ريال وخمسين هللة"), "10.50 SAR")
        self.assertEqual(t("خمسة دراهم وخمس وعشرين فلس"), "5.25 AED")
        self.assertEqual(t("خمسين هللة"), "0.50 SAR")
        self.assertEqual(t("جنيه وخمسين قرش"), "1.50 EGP")

    def test_duals(self):
        self.assertEqual(t("دفعت ريالين"), "دفعت 2 SAR")
        self.assertEqual(t("درهمين"), "2 AED")

    def test_money_span(self):
        r = normalize("ادفع ميتين وخمسين ريال لو سمحت")
        self.assertEqual(r["spans"], [dict(type="money", raw="ميتين وخمسين ريال", value="250 SAR")])
        self.assertEqual(r["text"], "ادفع 250 SAR لو سمحت")


class Times(unittest.TestCase):
    def test_half_quarter_third(self):
        self.assertEqual(t("الساعة تلاتة ونص العصر"), "الساعة 15:30")
        self.assertEqual(t("الساعة تلاتة ونص الصبح"), "الساعة 03:30")
        self.assertEqual(t("الساعة تلاتة ونص"), "الساعة 03:30")
        self.assertEqual(t("الساعة خمسة وربع المسا"), "الساعة 17:15")
        self.assertEqual(t("الساعة سبعة إلا ربع"), "الساعة 06:45")
        self.assertEqual(t("الساعة تسعة وتلت"), "الساعة 09:20")
        self.assertEqual(t("الساعة عشرة الا تلت بالليل"), "الساعة 21:40")

    def test_minutes(self):
        self.assertEqual(t("الساعة عشرة وخمسة"), "الساعة 10:05")
        self.assertEqual(t("الساعة اتناشر وعشرين دقيقة الظهر"), "الساعة 12:20")
        self.assertEqual(t("الساعة واحدة الا خمسة"), "الساعة 12:55")
        self.assertEqual(t("الساعة تمانية ونص وخمسة"), "الساعة 08:35")

    def test_msa_ordinals(self):
        self.assertEqual(t("الساعة الثالثة والنصف مساءً"), "الساعة 15:30")
        self.assertEqual(t("الساعة الحادية عشرة صباحا"), "الساعة 11:00")
        self.assertEqual(t("الساعة الثانية عشرة ظهرا"), "الساعة 12:00")

    def test_period_without_saa(self):
        self.assertEqual(t("نتقابل تلاتة ونص العصر"), "نتقابل 15:30")
        self.assertEqual(t("كيلو ونص"), "كيلو ونص")

    def test_time_span(self):
        r = normalize("موعدك الساعة أربعة العصر")
        self.assertEqual(r["spans"], [dict(type="time", raw="أربعة العصر", value="16:00")])


class Dates(unittest.TestCase):
    def test_dates_with_year(self):
        self.assertEqual(t("خمسة عشر أكتوبر ألفين وستة وعشرين"), "2026-10-15")
        self.assertEqual(t("يوم الخميس خمسة عشر أكتوبر ٢٠٢٦"), "2026-10-15")
        self.assertEqual(t("الأول من يناير سنة ألفين وسبعة وعشرين"), "2027-01-01")
        self.assertEqual(t("عشرين شهر تلاتة ٢٠٢٦"), "2026-03-20")
        self.assertEqual(t("تلاتة تشرين الأول ألفين وخمسة وعشرين"), "2025-10-03")
        self.assertEqual(t("الخامس والعشرين من ديسمبر 2026"), "2026-12-25")
        self.assertEqual(t("الحادي عشر من سبتمبر ألفين وواحد"), "2001-09-11")

    def test_no_year_no_date(self):
        self.assertEqual(t("خمسة عشر أكتوبر"), "15 أكتوبر")

    def test_invalid_day(self):
        self.assertEqual(t("تلاتين فبراير ٢٠٢٦"), "30 فبراير 2026")

    def test_date_span(self):
        r = normalize("الموعد يوم الخميس خمسة عشر أكتوبر ٢٠٢٦ إن شاء الله")
        self.assertEqual(r["spans"], [dict(type="date", raw="يوم الخميس خمسة عشر أكتوبر ٢٠٢٦", value="2026-10-15")])


class Emails(unittest.TestCase):
    def test_latin_words(self):
        self.assertEqual(t("ايميلي sara dot ali at gmail dot com"), "ايميلي sara.ali@gmail.com")

    def test_arabic_script_tokens(self):
        self.assertEqual(t("ايميلي sara نقطة ali آت جيميل دوت كوم"), "ايميلي sara.ali@gmail.com")
        self.assertEqual(t("الإيميل اس ايه ار ايه at هوتميل دوت كوم"), "الإيميل sara@hotmail.com")

    def test_letters_digits_underscore(self):
        self.assertEqual(t("a b واحد اتنين at yahoo dot com"), "ab12@yahoo.com")
        self.assertEqual(t("omar underscore k at outlook dot sa"), "omar_k@outlook.sa")

    def test_ambiguous_word_not_a_letter(self):
        self.assertEqual(t("ايميلي في sara at gmail dot com"), "ايميلي في sara@gmail.com")

    def test_needs_domain(self):
        self.assertEqual(t("I am at home"), "I am at home")

    def test_email_span(self):
        r = normalize("sara at gmail dot com")
        self.assertEqual(r["spans"], [dict(type="email", raw="sara at gmail dot com", value="sara@gmail.com")])


class OrderIds(unittest.TestCase):
    def test_letters_then_digits(self):
        self.assertEqual(t("رقم الطلب ايه بي واحد اتنين تلاتة اربعة"), "رقم الطلب AB-1234")
        self.assertEqual(t("الكود اكس واي زد تسعة تسعة"), "الكود XYZ-99")
        self.assertEqual(t("order A B 1234"), "order AB-1234")
        self.assertEqual(t("رقم الحجز كيو داش سبعة سبعة"), "رقم الحجز Q-77")

    def test_single_letter_needs_trigger(self):
        self.assertEqual(t("رقم الطلب جي خمسة"), "رقم الطلب G-5")
        self.assertEqual(t("في خمسة ستة سبعة"), "في 567")

    def test_order_span(self):
        r = normalize("ايه بي واحد اتنين")
        self.assertEqual(r["spans"], [dict(type="order_id", raw="ايه بي واحد اتنين", value="AB-12")])


class Cli(unittest.TestCase):
    def run_cli(self, text, *args):
        out = subprocess.run([sys.executable, "-m", "arabic_itn", *args], input=text, capture_output=True,
                             text=True, check=True, cwd=os.path.dirname(HERE)).stdout
        return [json.loads(line) for line in out.splitlines()]

    def test_one_json_object_per_line(self):
        rows = self.run_cli("المبلغ ميتين وخمسين ريال\n\nرقمي صفر خمسة صفر واحد اتنين تلاتة اربعة خمسة ستة سبعة\n")
        self.assertEqual([r["text"] for r in rows], ["المبلغ 250 SAR", "رقمي +966501234567"])
        self.assertEqual(rows[0]["spans"][0]["type"], "money")

    def test_country_flag(self):
        rows = self.run_cli("صفر خمسة صفر واحد اتنين تلاتة اربعة خمسة ستة سبعة", "--country", "AE")
        self.assertEqual(rows[0]["text"], "+971501234567")


class Fixtures(unittest.TestCase):
    """tests/cases.tsv: one "utterance<TAB>expected text" pair per line; # starts a comment."""

    def test_cases(self):
        cases = []
        with open(os.path.join(HERE, "cases.tsv"), encoding="utf-8") as f:
            for n, line in enumerate(f, 1):
                if line.strip() and not line.startswith("#"):
                    src, want = line.rstrip("\n").split("\t")
                    cases.append((n, src, want))
        self.assertGreaterEqual(len(cases), 200)
        for n, src, want in cases:
            with self.subTest(line=n, src=src):
                self.assertEqual(t(src), want)


if __name__ == "__main__":
    unittest.main()
