import unittest

from arabic_itn import normalize


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


if __name__ == "__main__":
    unittest.main()
