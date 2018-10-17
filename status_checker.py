import os
import redis
import json
from yandex_money.api import ExternalPayment
import requests


def status_check():
    r = redis.StrictRedis()

    while True:
        all_operations = r.scan_iter()
        for operation in all_operations:
            if r.get(operation) is None:
                continue
            operation_data = json.loads(r.get(operation))

            url_for_answer = operation_data['url_for_answer']
            ext_auth_success_uri = operation_data['ext_auth_success_uri']
            ext_auth_fail_uri = operation_data['ext_auth_fail_uri']
            request_token = operation_data['request_token']
            yandex_client_id = operation_data['yandex_client_id']
            payment_request_id = operation

            external_payment_process_options = {
                "request_id": payment_request_id,
                "ext_auth_success_uri": ext_auth_success_uri,
                "ext_auth_fail_uri": ext_auth_fail_uri,
                "request_token": request_token,
            }

            yandex_instance_id_key = os.environ.get('YANDEX_MONEY_INSTANCE_ID_KEY', None)
            if yandex_instance_id_key is None:
                response_payment_instance = ExternalPayment.get_instance_id(yandex_client_id)
                yandex_instance_id_key = response_payment_instance['instance_id']
                os.environ['YANDEX_MONEY_INSTANCE_ID_KEY'] = yandex_instance_id_key

            external_payment = ExternalPayment(yandex_instance_id_key)

            response_for_external_payment_process = external_payment.process(external_payment_process_options)

            status_response_external_payment_process = response_for_external_payment_process['status']

            if status_response_external_payment_process == 'success':
                return 'success'
            elif status_response_external_payment_process == 'refused':
                return 'refused'
            elif status_response_external_payment_process == 'in_progress':
                return
            else:
                return
