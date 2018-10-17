import redis
import json
from yandex_api import api
import requests
from . import config
import time


# проверка статуса транзакции по списку из редиса и отправляем запрос со статусом по указаннному юрл
def status_check():
    r = redis.StrictRedis(config.redis_db)

    while True:
        all_operations = r.scan_iter()
        for operation in all_operations:
            if r.get(operation) is None:
                continue
            operation_data = json.loads(r.get(operation))

            url_for_answer = operation_data['url_for_answer']
            yandex_auth_success_uri = operation_data['yandex_auth_success_uri']
            yandex_auth_fail_uri = operation_data['yandex_auth_fail_uri']
            request_token = operation_data['request_token']
            yandex_client_id = operation_data['yandex_client_id']
            payment_request_id = operation

            status = api.check_status(yandex_client_id,
                                      payment_request_id,
                                      yandex_auth_success_uri,
                                      yandex_auth_fail_uri)

            if status is None:
                continue

            if status["value"] == "in_progress":
                send_operation_info(url_for_answer, status["value"], payment_request_id)

            # если статус транзакции ошибка, то удаляем из редис
            elif status["value"] == "refused":
                send_operation_info(url_for_answer, status["value"], payment_request_id)
                r.delete(operation)
            # если статус транзакции успех, то удаляем из редис
            elif status["value"] == "success":
                send_operation_info(url_for_answer, status["value"], payment_request_id, invoice_id=status["invoice_id"])
                r.delete(operation)

        time.sleep(config.check_status_sleep)


def send_operation_info(url_for_answer, status, payment_request_id, error=None, invoice_id=None):
    data = {
        "error": error,
        "status": status,
        "payment_request_id": payment_request_id,
        "invoice_id": invoice_id
    }

    try:
        requests.post(url_for_answer, data=data)
    except Exception as e:
        pass
