"""Pure-function unit tests for engagement service (no DB)."""
from __future__ import annotations
import datetime as dt
import pytest

from app.modules.engagement.service import (
    compute_streak_reward, evaluate_quiz, compute_quiz_reward,
    is_same_utc_day, is_consecutive_day, MAX_OPEN_PREDICTIONS_PER_USER,
    REWARD_QUIZ_PER_CORRECT, REWARD_QUIZ_PERFECT_BONUS,
    REWARD_LOGIN_STREAK_BASE, REWARD_LOGIN_STREAK_CAP_DAYS,
)


class TestStreakReward:
    def test_zero_or_negative(self):
        assert compute_streak_reward(0) == 0.0
        assert compute_streak_reward(-3) == 0.0

    def test_day_one_is_base(self):
        assert compute_streak_reward(1) == pytest.approx(REWARD_LOGIN_STREAK_BASE)

    def test_day_two_higher_than_day_one(self):
        assert compute_streak_reward(2) > compute_streak_reward(1)

    def test_caps_at_seven(self):
        # 8° giorno = stesso reward del 7° (cap)
        assert compute_streak_reward(8) == pytest.approx(compute_streak_reward(REWARD_LOGIN_STREAK_CAP_DAYS))
        assert compute_streak_reward(100) == pytest.approx(compute_streak_reward(REWARD_LOGIN_STREAK_CAP_DAYS))


class TestUtcDayHelpers:
    def test_same_day(self):
        a = dt.datetime(2026, 6, 5, 9, 0, 0, tzinfo=dt.timezone.utc)
        b = dt.datetime(2026, 6, 5, 23, 59, 0, tzinfo=dt.timezone.utc)
        assert is_same_utc_day(a, b) is True

    def test_different_day(self):
        a = dt.datetime(2026, 6, 5, 9, 0, 0, tzinfo=dt.timezone.utc)
        b = dt.datetime(2026, 6, 6, 0, 5, 0, tzinfo=dt.timezone.utc)
        assert is_same_utc_day(a, b) is False

    def test_consecutive(self):
        a = dt.datetime(2026, 6, 5, 9, 0, 0, tzinfo=dt.timezone.utc)
        b = dt.datetime(2026, 6, 6, 0, 5, 0, tzinfo=dt.timezone.utc)
        assert is_consecutive_day(a, b) is True

    def test_not_consecutive(self):
        a = dt.datetime(2026, 6, 5, 9, 0, 0, tzinfo=dt.timezone.utc)
        b = dt.datetime(2026, 6, 7, 0, 5, 0, tzinfo=dt.timezone.utc)
        assert is_consecutive_day(a, b) is False


class TestEvaluateQuiz:
    def _q(self, opts, correct):
        return {"text": "?", "options": opts, "correct_index": correct}

    def test_empty(self):
        out = evaluate_quiz(questions=[], answers=[])
        assert out["correct"] == 0 and out["total"] == 0 and out["perfect"] is False

    def test_perfect(self):
        qs = [self._q(["a", "b"], 0), self._q(["x", "y"], 1)]
        out = evaluate_quiz(questions=qs, answers=[0, 1])
        assert out == {"correct": 2, "total": 2, "score": 1.0, "perfect": True}

    def test_partial(self):
        qs = [self._q(["a", "b"], 0), self._q(["x", "y"], 1), self._q(["m", "n"], 0)]
        out = evaluate_quiz(questions=qs, answers=[0, 1, 1])
        assert out["correct"] == 2 and out["total"] == 3 and out["perfect"] is False

    def test_short_answers_default_wrong(self):
        qs = [self._q(["a"], 0), self._q(["a"], 0)]
        out = evaluate_quiz(questions=qs, answers=[0])  # missing 2nd answer
        assert out["correct"] == 1


class TestQuizReward:
    def test_zero_correct(self):
        assert compute_quiz_reward(correct=0, perfect=False) == 0.0

    def test_partial(self):
        # 3 corrette × 0.5 = 1.5
        assert compute_quiz_reward(correct=3, perfect=False) == pytest.approx(3 * REWARD_QUIZ_PER_CORRECT)

    def test_perfect_bonus(self):
        # 5 corrette × 0.5 + 1.0 bonus
        out = compute_quiz_reward(correct=5, perfect=True)
        assert out == pytest.approx(5 * REWARD_QUIZ_PER_CORRECT + REWARD_QUIZ_PERFECT_BONUS)


class TestSecurityInvariants:
    """Test design-level: garanzie strutturali (lette dal modulo)."""

    def test_max_open_predictions_limit_sane(self):
        assert 1 <= MAX_OPEN_PREDICTIONS_PER_USER <= 10
