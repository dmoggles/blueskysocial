import unittest
from blueskysocial.convos.filters import (
    UnreadCount,
    Participant,
    LastMessageTime,
    SentAt,
    GT,
    Eq,
    Neq,
    LT,
    And,
    Or,
    Not,
)
import datetime as dt


class MockConvo:
    def __init__(self, unread_count: int):
        self.unread_count = unread_count
        self.participant = "user123"
        self.last_message_time = dt.datetime(2023, 10, 1, 12, 0, 0)
        self.opened = True
        self.convo_id = "convo123"
        self.last_message = ""


class TestUnreadCount(unittest.TestCase):
    def test_evaluate(self):
        convo = MockConvo(unread_count=5)
        self.assertEqual(UnreadCount.extract(convo), 5)

    def test_value(self):
        self.assertEqual(UnreadCount.rhs_transform(10), 10)


class MockConvoWithParticipant(MockConvo):
    def __init__(self, participant: str):
        super().__init__(unread_count=0)
        self.participant = participant


class TestParticipant(unittest.TestCase):
    def test_evaluate(self):
        convo = MockConvoWithParticipant(participant="user123")
        self.assertEqual(Participant.extract(convo), "user123")

    def test_value(self):
        self.assertEqual(Participant.rhs_transform("user123"), "user123")


class MockConvoWithLastMessageTime(MockConvo):
    def __init__(self, last_message_time: dt.datetime):
        super().__init__(unread_count=0)
        self.last_message_time = last_message_time


class TestLastMessageTime(unittest.TestCase):
    def test_evaluate(self):
        convo = MockConvoWithLastMessageTime(
            last_message_time=dt.datetime(2023, 10, 1, 12, 0, 0)
        )
        self.assertEqual(
            LastMessageTime.extract(convo), dt.datetime(2023, 10, 1, 12, 0, 0)
        )

    def test_value_with_string(self):
        self.assertEqual(
            LastMessageTime.rhs_transform("2023-10-01"), dt.datetime(2023, 10, 1)
        )

    def test_value_with_dt_string(self):
        self.assertEqual(
            LastMessageTime.rhs_transform("2023-10-01 12:00:00"),
            dt.datetime(2023, 10, 1, 12, 0, 0),
        )

    def test_value_with_datetime(self):
        self.assertEqual(
            LastMessageTime.rhs_transform(dt.datetime(2023, 10, 1, 12, 0, 0)),
            dt.datetime(2023, 10, 1, 12, 0, 0),
        )

    def test_value_with_date(self):
        self.assertEqual(
            LastMessageTime.rhs_transform(dt.date(2023, 10, 1)),
            dt.datetime(2023, 10, 1),
        )

    def test_value_with_invalid_string(self):
        with self.assertRaises(ValueError):
            LastMessageTime.rhs_transform("invalid")


class MockMessage:
    def __init__(self, sent_at: dt.datetime):
        self.sent_at = sent_at
        self.text = "Test message"
        self.convo = MockConvo(unread_count=0)


class TestSentAt(unittest.TestCase):
    def test_evaluate(self):
        message = MockMessage(sent_at=dt.datetime(2023, 10, 1, 12, 0, 0))
        self.assertEqual(SentAt.extract(message), dt.datetime(2023, 10, 1, 12, 0, 0))

    def test_value(self):
        self.assertEqual(
            SentAt.rhs_transform("2023-10-01 12:00:00"),
            dt.datetime(2023, 10, 1, 12, 0, 0),
        )


class TestGT(unittest.TestCase):
    def test_evaluate_true(self):
        convo = MockConvo(unread_count=10)
        gt_filter = GT(UnreadCount, 5)
        self.assertTrue(gt_filter(convo))

    def test_evaluate_false(self):
        convo = MockConvo(unread_count=3)
        gt_filter = GT(UnreadCount, 5)
        self.assertFalse(gt_filter(convo))

    def test_evaluate_equal(self):
        convo = MockConvo(unread_count=5)
        gt_filter = GT(UnreadCount, 5)
        self.assertFalse(gt_filter(convo))


class TestEq(unittest.TestCase):
    def test_evaluate_true(self):
        convo = MockConvo(unread_count=5)
        eq_filter = Eq(UnreadCount, 5)
        self.assertTrue(eq_filter(convo))

    def test_evaluate_false(self):
        convo = MockConvo(unread_count=3)
        eq_filter = Eq(UnreadCount, 5)
        self.assertFalse(eq_filter(convo))

    def test_evaluate_with_participant_true(self):
        convo = MockConvoWithParticipant(participant="user123")
        eq_filter = Eq(Participant, "user123")
        self.assertTrue(eq_filter(convo))

    def test_evaluate_with_participant_false(self):
        convo = MockConvoWithParticipant(participant="user456")
        eq_filter = Eq(Participant, "user123")
        self.assertFalse(eq_filter(convo))

    def test_evaluate_with_last_message_time_true(self):
        convo = MockConvoWithLastMessageTime(
            last_message_time=dt.datetime(2023, 10, 1, 12, 0, 0)
        )
        eq_filter = Eq(LastMessageTime, "2023-10-01 12:00:00")
        self.assertTrue(eq_filter(convo))

    def test_evaluate_with_last_message_time_false(self):
        convo = MockConvoWithLastMessageTime(
            last_message_time=dt.datetime(2023, 10, 1, 12, 0, 0)
        )
        eq_filter = Eq(LastMessageTime, "2023-10-02 12:00:00")
        self.assertFalse(eq_filter(convo))


class TestNeq(unittest.TestCase):
    def test_evaluate_true(self):
        convo = MockConvo(unread_count=5)
        neq_filter = Neq(UnreadCount, 3)
        self.assertTrue(neq_filter(convo))

    def test_evaluate_false(self):
        convo = MockConvo(unread_count=5)
        neq_filter = Neq(UnreadCount, 5)
        self.assertFalse(neq_filter(convo))

    def test_evaluate_with_participant_true(self):
        convo = MockConvoWithParticipant(participant="user123")
        neq_filter = Neq(Participant, "user456")
        self.assertTrue(neq_filter(convo))

    def test_evaluate_with_participant_false(self):
        convo = MockConvoWithParticipant(participant="user123")
        neq_filter = Neq(Participant, "user123")
        self.assertFalse(neq_filter(convo))

    def test_evaluate_with_last_message_time_true(self):
        convo = MockConvoWithLastMessageTime(
            last_message_time=dt.datetime(2023, 10, 1, 12, 0, 0)
        )
        neq_filter = Neq(LastMessageTime, "2023-10-02 12:00:00")
        self.assertTrue(neq_filter(convo))

    def test_evaluate_with_last_message_time_false(self):
        convo = MockConvoWithLastMessageTime(
            last_message_time=dt.datetime(2023, 10, 1, 12, 0, 0)
        )
        neq_filter = Neq(LastMessageTime, "2023-10-01 12:00:00")
        self.assertFalse(neq_filter(convo))


class TestLT(unittest.TestCase):
    def test_evaluate_true(self):
        convo = MockConvo(unread_count=3)
        lt_filter = LT(UnreadCount, 5)
        self.assertTrue(lt_filter(convo))

    def test_evaluate_false(self):
        convo = MockConvo(unread_count=7)
        lt_filter = LT(UnreadCount, 5)
        self.assertFalse(lt_filter(convo))

    def test_evaluate_equal(self):
        convo = MockConvo(unread_count=5)
        lt_filter = LT(UnreadCount, 5)
        self.assertFalse(lt_filter(convo))

    def test_evaluate_with_participant_true(self):
        convo = MockConvoWithParticipant(participant="user123")
        lt_filter = LT(Participant, "user456")
        self.assertTrue(lt_filter(convo))

    def test_evaluate_with_participant_false(self):
        convo = MockConvoWithParticipant(participant="user123")
        lt_filter = LT(Participant, "user123")
        self.assertFalse(lt_filter(convo))

    def test_evaluate_with_last_message_time_true(self):
        convo = MockConvoWithLastMessageTime(
            last_message_time=dt.datetime(2023, 10, 1, 12, 0, 0)
        )
        lt_filter = LT(LastMessageTime, "2023-10-02 12:00:00")
        self.assertTrue(lt_filter(convo))

    def test_evaluate_with_last_message_time_false(self):
        convo = MockConvoWithLastMessageTime(
            last_message_time=dt.datetime(2023, 10, 1, 12, 0, 0)
        )
        lt_filter = LT(LastMessageTime, "2023-10-01 12:00:00")
        self.assertFalse(lt_filter(convo))


class TestAnd(unittest.TestCase):
    def test_evaluate_true(self):
        convo = MockConvo(unread_count=5)
        and_filter = And(GT(UnreadCount, 3), LT(UnreadCount, 10))
        self.assertTrue(and_filter(convo))

    def test_evaluate_false(self):
        convo = MockConvo(unread_count=5)
        and_filter = And(GT(UnreadCount, 3), LT(UnreadCount, 5))
        self.assertFalse(and_filter(convo))

    def test_evaluate_all_true(self):
        convo = MockConvo(unread_count=5)
        and_filter = And(GT(UnreadCount, 3), LT(UnreadCount, 10), Eq(UnreadCount, 5))
        self.assertTrue(and_filter(convo))

    def test_evaluate_one_false(self):
        convo = MockConvo(unread_count=5)
        and_filter = And(GT(UnreadCount, 3), LT(UnreadCount, 10), Eq(UnreadCount, 4))
        self.assertFalse(and_filter(convo))

    def test_evaluate_with_participant_true(self):
        convo = MockConvoWithParticipant(participant="user123")
        and_filter = And(Eq(Participant, "user123"), Neq(Participant, "user456"))
        self.assertTrue(and_filter(convo))

    def test_evaluate_with_participant_false(self):
        convo = MockConvoWithParticipant(participant="user123")
        and_filter = And(Eq(Participant, "user123"), Neq(Participant, "user123"))
        self.assertFalse(and_filter(convo))

    def test_evaluate_with_last_message_time_true(self):
        convo = MockConvoWithLastMessageTime(
            last_message_time=dt.datetime(2023, 10, 1, 12, 0, 0)
        )
        and_filter = And(
            Eq(LastMessageTime, "2023-10-01 12:00:00"),
            Neq(LastMessageTime, "2023-10-02 12:00:00"),
        )
        self.assertTrue(and_filter(convo))

    def test_evaluate_with_last_message_time_false(self):
        convo = MockConvoWithLastMessageTime(
            last_message_time=dt.datetime(2023, 10, 1, 12, 0, 0)
        )
        and_filter = And(
            Eq(LastMessageTime, "2023-10-01 12:00:00"),
            Neq(LastMessageTime, "2023-10-01 12:00:00"),
        )
        self.assertFalse(and_filter(convo))


class TestOr(unittest.TestCase):
    def test_evaluate_true(self):
        convo = MockConvo(unread_count=5)
        or_filter = Or(GT(UnreadCount, 3), LT(UnreadCount, 10))
        self.assertTrue(or_filter(convo))

    def test_evaluate_false(self):
        convo = MockConvo(unread_count=5)
        or_filter = Or(GT(UnreadCount, 10), LT(UnreadCount, 3))
        self.assertFalse(or_filter(convo))

    def test_evaluate_one_true(self):
        convo = MockConvo(unread_count=5)
        or_filter = Or(GT(UnreadCount, 3), LT(UnreadCount, 3))
        self.assertTrue(or_filter(convo))

    def test_evaluate_with_participant_true(self):
        convo = MockConvoWithParticipant(participant="user123")
        or_filter = Or(Eq(Participant, "user123"), Neq(Participant, "user456"))
        self.assertTrue(or_filter(convo))

    def test_evaluate_with_participant_false(self):
        convo = MockConvoWithParticipant(participant="user123")
        or_filter = Or(Eq(Participant, "user456"), Neq(Participant, "user123"))
        self.assertFalse(or_filter(convo))

    def test_evaluate_with_last_message_time_true(self):
        convo = MockConvoWithLastMessageTime(
            last_message_time=dt.datetime(2023, 10, 1, 12, 0, 0)
        )
        or_filter = Or(
            Eq(LastMessageTime, "2023-10-01 12:00:00"),
            Neq(LastMessageTime, "2023-10-02 12:00:00"),
        )
        self.assertTrue(or_filter(convo))

    def test_evaluate_with_last_message_time_false(self):
        convo = MockConvoWithLastMessageTime(
            last_message_time=dt.datetime(2023, 10, 1, 12, 0, 0)
        )
        or_filter = Or(
            Eq(LastMessageTime, "2023-10-02 12:00:00"),
            Neq(LastMessageTime, "2023-10-01 12:00:00"),
        )
        self.assertFalse(or_filter(convo))


class TestNot(unittest.TestCase):
    def test_evaluate_true(self):
        convo = MockConvo(unread_count=5)
        not_filter = Not(GT(UnreadCount, 10))
        self.assertTrue(not_filter(convo))

    def test_evaluate_false(self):
        convo = MockConvo(unread_count=5)
        not_filter = Not(GT(UnreadCount, 3))
        self.assertFalse(not_filter(convo))

    def test_evaluate_with_participant_true(self):
        convo = MockConvoWithParticipant(participant="user123")
        not_filter = Not(Eq(Participant, "user456"))
        self.assertTrue(not_filter(convo))

    def test_evaluate_with_participant_false(self):
        convo = MockConvoWithParticipant(participant="user123")
        not_filter = Not(Eq(Participant, "user123"))
        self.assertFalse(not_filter(convo))

    def test_evaluate_with_last_message_time_true(self):
        convo = MockConvoWithLastMessageTime(
            last_message_time=dt.datetime(2023, 10, 1, 12, 0, 0)
        )
        not_filter = Not(Eq(LastMessageTime, "2023-10-02 12:00:00"))
        self.assertTrue(not_filter(convo))

    def test_evaluate_with_last_message_time_false(self):
        convo = MockConvoWithLastMessageTime(
            last_message_time=dt.datetime(2023, 10, 1, 12, 0, 0)
        )
        not_filter = Not(Eq(LastMessageTime, "2023-10-01 12:00:00"))
        self.assertFalse(not_filter(convo))
