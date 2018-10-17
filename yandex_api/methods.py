import os
from yandex_money.api import ExternalPayment
from urllib.parse import urlencode, urlparse, urlunparse


# получение экземпляра платежного приложения
def get_yandex_instance_id_key(yandex_client_id):
    yandex_instance_id_key = os.environ.get('YANDEX_MONEY_INSTANCE_ID_KEY', None)

    if yandex_instance_id_key is None:
        response_payment_instance = ExternalPayment.get_instance_id(yandex_client_id)
        yandex_instance_id_key = response_payment_instance['instance_id']
        os.environ['YANDEX_MONEY_INSTANCE_ID_KEY'] = yandex_instance_id_key

    return yandex_instance_id_key


# запрос на создание платежной операции, возвращает идентификатор процесса платежа
def external_payment_request(external_payment, yandex_instance_id_key, yandex_wallet, amount, message=None):
    if message is None:
        message = "payment message from yandex-money-python"

    external_payment_request_data = {
        "pattern_id": "p2p",
        "instance_id": yandex_instance_id_key,
        "to": yandex_wallet,
        "amount": amount,
        "message": message
    }

    response_for_external_payment_request = external_payment.request(external_payment_request_data)

    status_response_external_payment_request = response_for_external_payment_request['status']
    if status_response_external_payment_request == 'refused':
        return

    payment_request_id = response_for_external_payment_request['request_id']

    payment_contract_amount = response_for_external_payment_request['contract_amount']
    payment_title = response_for_external_payment_request['title']

    return payment_request_id


# запрос на проверку статуса платежа
def external_payment_process(external_payment,
                             payment_request_id,
                             yandex_auth_success_uri,
                             yandex_auth_fail_uri,
                             yandex_client_id,
                             request_token=False):

    external_payment_process_options = {
        "request_id": payment_request_id,
        "ext_auth_success_uri": yandex_auth_success_uri,
        "ext_auth_fail_uri": yandex_auth_fail_uri,
        "request_token": request_token,
        "yandex_client_id": yandex_client_id,
    }

    response_for_external_payment_process = external_payment.process(external_payment_process_options)

    status_response_external_payment_process = response_for_external_payment_process['status']

    # транзакция завершилась успешно
    if status_response_external_payment_process == 'success':
        return {"key": "status", "value": "success"}

    # транзакция завершилась с ошибкой
    elif status_response_external_payment_process == 'refused':
        return {"key": "status", "value": "refused"}

    # транзакция в процессе
    elif status_response_external_payment_process == 'in_progress':
        return {"key": "status", "value": "process"}

    # транзакция ожидает подтверждения операции пользователем по определенному адресу
    else:
        redirect_url_parse = urlparse(response_for_external_payment_process['acs_uri'])
        redirect_url_query = urlencode(response_for_external_payment_process['acs_params'])
        redirect_url_for_access_pay = urlunparse((redirect_url_parse.scheme,
                                                  redirect_url_parse.netloc,
                                                  redirect_url_parse.path,
                                                  redirect_url_parse.params,
                                                  redirect_url_query,
                                                  redirect_url_parse.fragment))

        return {"key": "access_pay", "value": redirect_url_for_access_pay}

