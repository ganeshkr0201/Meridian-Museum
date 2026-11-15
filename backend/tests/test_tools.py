"""Tests for walking distance, opening hours, and crowd status tools."""
import pytest
from app.tools.walking_distance import get_walking_distance
from app.tools.opening_hours import check_opening_hours, gallery_visit_fits
from app.tools.crowd_status import get_crowd_status, set_crowd_state, reset_crowd_states
from app.models.exhibit import CrowdState


def test_walking_same_gallery():
    result = get_walking_distance("G01", "G01")
    assert result.distance_m == 0.0
    assert result.walk_minutes == 0.0


def test_walking_adjacent_galleries():
    result = get_walking_distance("G01", "G02")
    assert result.distance_m > 0
    assert result.walk_minutes > 0


def test_walking_all_pairs():
    galleries = ["G01", "G02", "G03", "G04"]
    for src in galleries:
        for dst in galleries:
            r = get_walking_distance(src, dst)
            assert r.walk_minutes >= 0


def test_walking_accessible_avoids_stairs():
    # G01→G03 has a stair shortcut; accessible mode should use longer path
    normal = get_walking_distance("G01", "G03", accessible_mode=False)
    accessible = get_walking_distance("G01", "G03", accessible_mode=True)
    assert accessible.distance_m >= normal.distance_m


def test_opening_hours_open():
    result = check_opening_hours("G01", "10:00")
    assert result.is_open is True


def test_opening_hours_closed_before_open():
    result = check_opening_hours("G01", "08:00")
    assert result.is_open is False


def test_opening_hours_closed_after_close():
    result = check_opening_hours("G01", "18:00")
    assert result.is_open is False


def test_opening_hours_art_gallery_later_open():
    # G03 opens at 10:00
    result = check_opening_hours("G03", "09:30")
    assert result.is_open is False
    result2 = check_opening_hours("G03", "10:30")
    assert result2.is_open is True


def test_gallery_visit_fits():
    fits, reason = gallery_visit_fits("G01", 10.0, 15, "09:00")
    assert fits is True


def test_gallery_visit_exceeds_close():
    # 9:00 start + 7h55m offset + 15 min > 17:00
    fits, _ = gallery_visit_fits("G01", 475.0, 15, "09:00")
    assert fits is False


def test_crowd_status_default_normal():
    reset_crowd_states()
    result = get_crowd_status("G01")
    assert result.crowd_state == CrowdState.NORMAL
    assert result.is_visitable is True


def test_crowd_status_set_busy():
    set_crowd_state("G02", CrowdState.BUSY)
    result = get_crowd_status("G02")
    assert result.crowd_state == CrowdState.BUSY
    assert result.penalty_minutes > 0
    reset_crowd_states()


def test_crowd_status_closed_not_visitable():
    set_crowd_state("G03", CrowdState.CLOSED)
    result = get_crowd_status("G03")
    assert result.is_visitable is False
    reset_crowd_states()
