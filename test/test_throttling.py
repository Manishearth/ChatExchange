import time
import logging

from chatexchange import requestexecutor


logger = logging.getLogger(__name__)


def test_throttling():
    """
    Tests the behaviour of the executor, taking advantage of throttling
    but with no failures or retries.
    """

    target_interval = 1.0
    max_interval = 1.1

    logger.info("Creating RequestExecutor")
    with requestexecutor.RequestExecutor(
        min_interval=target_interval,
        max_attempts=2
    ) as executor:
        assert executor._thread.is_alive()

        times = []

        def successful_consecutively(value):
            times.append(time.time())
            if len(times) > 1:
                interval = times[-1] - times[-2]

                assert interval >= target_interval, "interval %s < %s" % (interval, target_interval)
                assert interval <= max_interval

            return value

        retry_times = []
        def retry_in_5_first_time(value):
            times.append(time.time())
            retry_times.append(time.time())
            if len(retry_times) == 1:
                raise requestexecutor.RequestAttemptFailed(5.0)
            return value

        a = executor.submit(successful_consecutively, 'a')
        b = executor.submit(successful_consecutively, 'b')
        c = executor.submit(successful_consecutively, 'c')
        d = executor.submit(successful_consecutively, 'd')
        e = executor.submit(retry_in_5_first_time, 'e')
        f = executor.submit(retry_in_5_first_time, 'f')
        g = executor.submit(retry_in_5_first_time, 'g')

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
    assert 2.9 <= intervals[-1] <= 3.1  # the retried call


if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)
    test_throttling()
