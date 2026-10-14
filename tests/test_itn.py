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


if __name__ == "__main__":
    unittest.main()
