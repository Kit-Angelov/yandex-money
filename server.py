from aiohttp import web
import asyncio
import redis
import json
from yandex_api.api import pay
from status_checker import status_check
import config
import argparse


async def handler_payment(request):
    data = await request.post()  # получаем данные от главного сервера
    try:  # проверяем полноту данных
        url_for_answer = data['url_for_answer']
        yandex_access_dict = {
            'yandex_wallet': data['YANDEX_WALLET'],
            'yandex_client_id': data['YANDEX_CLIENT_ID'],
            'yandex_auth_success_uri': data['YANDEX_SUCCESS_URI'],
            'yandex_auth_fail_uri': data['YANDEX_FAIL_URI']
        }
        amount = float(data['amount'])
    except Exception as e:
        raise web.HTTPBadRequest(text=str(e))

    # создаем транзакцию в яндекс-деньгах. получаем идентификатор операции, юрл для подтвреждения пользователем платежа
    loop = asyncio.get_event_loop()
    redirect_url_access_pay, payment_request_id = await loop.run_in_executor(None, pay, amount, yandex_access_dict)

    # если все ок (транзакция создана)
    if redirect_url_access_pay is not None and payment_request_id is not None:
        response_content = {
            'redirect_url_access_pay': redirect_url_access_pay,
            'payment_request_id': payment_request_id
        }

        # добавляем в редис запись о созданной транзакции с необходимимыми данными для проверки статуса
        redis_content = {
            "url_for_answer": url_for_answer,
            "yandex_auth_success_uri": data['YANDEX_MONEY_SUCCESS_URI'],
            "yandex_auth_fail_uri": data['YANDEX_MONEY_FAIL_URI'],
            "request_token": False,
        }
        r = redis.StrictRedis(config.redis_host, config.redis_port, config.redis_db)
        r.set(payment_request_id, json.dumps(redis_content))

        # возвращаем на главнй сервер идентификатор транзакции и юрл редиректа клиента для подтверждения транзакции
        return web.json_response(response_content)
    else:
        raise web.HTTPBadRequest(text='operation already exist')


async def run():
    app = web.Application()
    app.add_routes([web.post('/pay', handler_payment)])

    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, status_check)
    return app


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="yandex-money-server")
    parser.add_argument('--port')
    args = parser.parse_args()

    app = run()
    web.run_app(app, port=args.port)