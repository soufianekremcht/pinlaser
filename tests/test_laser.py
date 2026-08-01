from laser import FRAME_TIME, MAX_SUBDIV, LaserEffect, subdivide_segment


class FakeSettings:
    trail_length = 40
    glow_radius = 28.0
    color = "#ff2a1a"


class FakeClock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


def make_laser(trail_length=40):
    laser = LaserEffect(FakeSettings())
    laser._settings.trail_length = trail_length
    clock = FakeClock()
    laser._clock = clock
    return laser, clock


def test_update_pos_appends_when_active():
    laser, _ = make_laser()
    laser.update_pos(10, 20, True)
    laser.update_pos(11, 21, True)
    assert len(laser._trail) == 2


def test_update_pos_skips_when_inactive():
    laser, _ = make_laser()
    laser.update_pos(10, 20, False)
    assert len(laser._trail) == 0


def test_trail_trimmed_to_max_length():
    laser, _ = make_laser(trail_length=5)
    for i in range(20):
        laser.update_pos(float(i), 0.0, True)
        laser._clock.t += FRAME_TIME
    assert len(laser._trail) <= 5


def test_trail_expires_after_duration():
    laser, clock = make_laser(trail_length=10)
    for _ in range(10):
        laser.update_pos(1.0, 1.0, True)
        clock.t += FRAME_TIME
    assert len(laser._trail) == 10
    clock.t += 10 * FRAME_TIME
    laser.update_pos(1.0, 1.0, True)
    assert len(laser._trail) == 1


def test_clear_empties_trail():
    laser, _ = make_laser()
    laser.update_pos(10, 20, True)
    laser.clear()
    assert len(laser._trail) == 0


def test_pos_updated_even_when_inactive():
    laser, _ = make_laser()
    laser.update_pos(30, 40, False)
    assert laser._pos == (30.0, 40.0)


def test_subdivide_preserves_endpoints_and_fades_increase():
    duration = 10 * FRAME_TIME
    now = 1.0
    p1 = (0.0, 0.0, now - duration)
    p2 = (100.0, 0.0, now)
    segs = subdivide_segment(p1, p2, now, duration)
    assert segs
    assert segs[0][0] == 0.0 and segs[0][1] == 0.0
    assert segs[-1][2] == 100.0 and segs[-1][3] == 0.0
    fades = [s[4] for s in segs]
    assert all(0.0 <= f <= 1.0 for f in fades)
    assert fades == sorted(fades)


def test_subdivide_count_capped():
    p1 = (0.0, 0.0, 0.0)
    p2 = (100000.0, 0.0, 1.0)
    segs = subdivide_segment(p1, p2, 1.0, 1.0)
    assert 1 <= len(segs) <= MAX_SUBDIV


def test_subdivide_empty_when_fully_expired():
    duration = 10 * FRAME_TIME
    p1 = (0.0, 0.0, 0.0)
    p2 = (1.0, 0.0, 0.0)
    assert subdivide_segment(p1, p2, 1.0, duration) == []
