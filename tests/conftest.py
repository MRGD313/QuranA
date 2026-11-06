"""فیکسچرهای مشترک آزمون‌ها."""
import sys
from pathlib import Path

import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from config import DB_PATH
from src.quran_repository import QuranRepository


def pytest_sessionstart(session):
    """اگر پایگاه داده آماده نیست، صریح هشدار بدهد تا skip با pass اشتباه نشود."""
    if not DB_PATH.exists():
        print(
            "\n[tests] data/quran.db missing: data-dependent tests will skip. "
            "Run scripts/prepare_data.py first.\n",
            file=sys.stderr,
        )


@pytest.fixture(scope="session")
def repo():
    if not DB_PATH.exists():
        pytest.skip("quran.db آماده نیست (prepare_data.py اجرا نشده)")
    r = QuranRepository(DB_PATH).connect()
    yield r
    r.close()


class FakeBaleClient:
    """کلاینت بله دورزدن‌شده برای آزمون منطق ربات (بدون شبکه)."""

    def __init__(self):
        self.sent = []            # (chat_id, text)
        self.docs = []            # (chat_id, file_path, caption)
        self.fail_document = None  # برای شبیه‌سازی خطای ارسال سند
        self.fail_message_contains = None  # خطا برای پیام‌های حاوی این عبارت

    def send_message(self, chat_id, text, reply_to_message_id=None):
        if self.fail_message_contains and self.fail_message_contains in text:
            raise RuntimeError("simulated message failure")
        self.sent.append((chat_id, text))
        return {"ok": True}

    def send_document(self, chat_id, file_path, caption=None):
        if self.fail_document is not None:
            raise self.fail_document
        self.docs.append((chat_id, Path(file_path), caption))
        return {"ok": True}

    # پیام‌های آخر
    def last_text(self):
        return self.sent[-1][1] if self.sent else None

    def texts(self):
        return [t for (_c, t) in self.sent]


@pytest.fixture
def fake_client():
    return FakeBaleClient()
