import time
import logging

from chatexchange import requestexecutor


logger = logging.getLogger(__name__)


def test_throttling():
    """
    Tests the behaviour of the executor, taking advantage of throttling
    but with no failures or retries.
    """

    min_interval = 0.9
    target_interval = 1.0
    max_interval = 1.1
    consecutive_penalty_factor = 1.5

    logger.info("Creating RequestExecutor")
    with requestexecutor.RequestExecutor(
        min_interval=target_interval,
        max_attempts=2,
        consecutive_penalty_factor=consecutive_penalty_factor,
    ) as executor:
        assert executor._thread.is_alive()

        times = []

        def simple_success(value):
            times.append(time.time())
            return value

        retry_times = []
        def retry_in_7_first_time(value):
            times.append(time.time())
            retry_times.append(time.time())
            if len(retry_times) == 1:
                raise requestexecutor.RequestAttemptFailed(7.0)
            return value

        a = executor.submit(simple_success, 'a')
        b = executor.submit(simple_success, 'b')
        c = executor.submit(simple_success, 'c')
        d = executor.submit(simple_success, 'd')
        e = executor.submit(retry_in_7_first_time, 'e')
        f = executor.submit(retry_in_7_first_time, 'f')
        g = executor.submit(retry_in_7_first_time, 'g')

        assert b.result() == 'b'
        assert a.result() == 'a'

        assert len(times) == 2

        assert executor._thread.is_alive()

        assert f.result() == 'f'
        assert not e.done()  # because it was retried
        assert e.result() == 'e'
        assert e.done()

    logger.info("RequestExecutor has shut down")

    intervals = [b - a for (a, b) in zip(times[0:], times[1:])]

    logger.info('times: %r', times)
    logger.info('intervals: %r', intervals)

    assert c.result() == 'c'
    assert d.result() == 'd'
    assert f.result() == 'f'
    assert g.result() == 'g'

    assert min_interval <= intervals[0] <= max_interval
    assert min_interval <= intervals[1] <= max_interval
    assert min_interval <= intervals[2] <= max_interval
    assert min_interval <= intervals[3] <= max_interval # request 5 is the failure
    assert (min_interval * consecutive_penalty_factor <= intervals[4]
            <= max_interval * consecutive_penalty_factor)
    assert min_interval <= intervals[5] <= max_interval
    interval_from_failure_to_success = times[-1] - times[4]
    logger.info('interval_from_failure_to_success = %r', interval_from_failure_to_success)
    assert 6.9 <= interval_from_failure_to_success <= 7.1

if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)
    test_throttling()
