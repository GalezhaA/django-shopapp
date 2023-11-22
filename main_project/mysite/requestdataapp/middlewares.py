from django.http import HttpRequest
import time

from django.shortcuts import render


def set_useragent_on_request_middleware(get_response):

    print('Initial call')

    def middleware(request: HttpRequest):
        print('before get response')
        request.user_agent = request.META['HTTP_USER_AGENT']
        response = get_response(request)
        print('after get response')
        return response

    return middleware


class CountRequestsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.requests_count = 0
        self.responses_count = 0
        self.exceptions_count = 0
        self.request_time = {}

    def __call__(self, request: HttpRequest):
        time_delay = 0
        if not self.request_time:
            print('Первый запрос')
        else:
            if round(time.time()) - self.request_time['time'] < time_delay and self.request_time['ip'] == request.META.get(
                    'REMOTE_ADDR'):
                print('Слишком быстро!')
                return render(request, 'requestdataapp/error-time.html')

        self.request_time = {'time': round(time.time()), 'ip': request.META.get('REMOTE_ADDR')}

        self.requests_count += 1
        print('Requests count:', self.requests_count)
        response = self.get_response(request)
        self.responses_count += 1
        print('Responses count:', self.responses_count)
        return response

    def process_exception(self, request: HttpRequest, exception: Exception):
        self.exceptions_count += 1
        print('got', self.exceptions_count, 'exceptions so far')