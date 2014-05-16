import Queue
import functools
import logging
import threading

import concurrent.futures
import time


logger = logging.getLogger(__name__)


class RequestExecutor(concurrent.futures.Executor):
    """
    An Executor which will run calls consecutively, rate-limited, and retries failures.

    see https://docs.python.org/3.4/library/concurrent.futures.html#concurrent.futures.Executor

    @iattr max_attempts:         The maximum number of times a request will be called/retried.
    @iattr min_interval:         The minimum amount of time that must elapse between request call invocations.
    """

    def __init__(self, min_interval=3.0, max_attempts=5):
        self.min_interval = min_interval
        self.max_attempts = max_attempts
        self._request_queue = Queue.PriorityQueue()
        self._new_requests = Queue.Queue()

        self._shutdown = False

        self._time = time.time()

        self._thread = threading.Thread(target=self._work)
        self._thread.daemon = False
        self._thread.start()

    def _work(self):
        logger.debug("Worker thread for %r starting", self)

        # keep working until we shut down submissions and there's nothing left to progress
        # the order of the queue .empty() calls below is significant
        while True:
            #not (self._shutdown and self._new_requests.empty() and self._request_queue.empty())
            global_interval_remaining = self._time - time.time()
            request = None

            if global_interval_remaining > 0:
                new_requests_wait_timeout = global_interval_remaining
            else:
                try:
                    request = self._request_queue.get_nowait()
                    assert not request.done()
                except Queue.Empty:
                    pass

                if request is not None:
                    logger.debug("Worker examining %r", request)
                    # check if the highest-priority request is allowed to run yet
                    interval_remaining = request._time - time.time()

                    if interval_remaining > 0:
                        # if not, we'll wait for new requests until it is
                        new_requests_wait_timeout = interval_remaining
                        self._request_queue.put(request)
                    else:
                        # if so, run it.
                        new_requests_wait_timeout = None

                        not_cancelled = request.running() or request.set_running_or_notify_cancel()
                        if not_cancelled:
                            logger.info("Worker attempting to run %r", request)
                            request._attempt()
                            self._time = time.time() + self.min_interval

                            # put the request back on the queue if it isn't done
                            if not request.done():
                                self._request_queue.put(request)
                        else:
                            logger.info("Ignoring cancelled request")

                    self._request_queue.task_done()
                else:
                    logger.debug("No actions in request queue. Waiting for activity on new request queue.")
                    new_requests_wait_timeout = 0.0

            try:
                new_request = None
                if new_requests_wait_timeout is not None:
                    # wait for new requests until we know we have an existing request to run.
                    logger.debug("Worker waiting for new requests (timeout=%s).", new_requests_wait_timeout)
                    new_request = self._new_requests.get(timeout=new_requests_wait_timeout)
                    self._request_queue.put(new_request)
                    self._new_requests.task_done()

                while True:
                    # put everything available into the request queue now, no waiting.
                    logger.debug("Worker loading all new requests, not waiting.")
                    new_request = self._new_requests.get_nowait()
                    self._request_queue.put(new_request)
                    self._new_requests.task_done()
            except Queue.Empty:
                if global_interval_remaining <= 0 and self._shutdown and request is None and new_request is None:
                    break

            logger.debug("Continuing loop - shutdown=%r, request=%r, new_request=%r",
                        self._shutdown, request, new_request)

        logger.info("worker thread done")


    def submit(self, fn, *args, **kwargs):
        if self._shutdown:
            raise RuntimeError("Executor already shutdown.")

        request = RequestFuture(self, fn, args, kwargs)

        self._new_requests.put(request)

        return request

    def shutdown(self, wait=True):
        if not self._shutdown:
            logger.info("Shutting down %r", self)

        self._shutdown = True

        if wait:
            logger.info("waiting for %s new requests and %s queued requests",
                        self._new_requests.qsize(), self._request_queue.qsize())
            self._new_requests.join()
            self._request_queue.join()
            logger.info("anticipated worker shutdown complete")


@functools.total_ordering
class RequestFuture(concurrent.futures.Future):
    """
    @iattr time:   The minimum time at which this request may next be attempted.
                   Lower times are processed first.
    @iattr future: The result of the request.
    @type  future: L{concurrent.futures.Future}
    """

    def __init__(self, executor, fn, args, kwargs):
        self._executor = executor
        self._fn = fn
        self._args = args
        self._kwargs = kwargs
        self._time = time.time()
        self._exceptions = []

        super(RequestFuture, self).__init__()

    def __eq__(self, other):
        return self._time == other._time

    def __lt__(self, other):
        return self._time < other._time

    def _attempt(self):
        """
        Attempts to run the request, if it isn't already .done().
        """
        assert not self.done()

        try:
            result = self._fn(*self._args, **self._kwargs)
            self.set_result(result)
        except RequestAttemptFailed as ex:
            self._time = time.time() + ex.min_interval
            self._exceptions.append(ex)
            if len(self._exceptions) >= self._executor.max_attempts:
                logger.info("Last attempt failed for request: %r", ex)
                self.set_exception(ex)
        except Exception as ex:
            logger.exception("Unexpected exception in request attempt")
            self._exceptions.append(ex)
            self.set_exception(ex)


class RequestAttemptFailed(Exception):
    """
    Raised to indicate that an attempt to run a request has failed, but may be retried.

    @iattr min_interval: The minimum amount of time which must elapse before a retry.
    @iattr exception:    The exception that caused the failure, or None.
    """
    def __init__(self, min_interval=0.0, exception=None):
        self.min_interval = min_interval
        self.exception = exception

        super(RequestAttemptFailed, self).__init__(min_interval, exception)
