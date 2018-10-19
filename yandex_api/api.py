import os
from yandex_money.api import ExternalPayment
from . import methods
from urllib.parse import urlencode, urlparse, urlunparse


def pay(amount, yandex_access):
    # определяем необходимые переменные для работы с yandex-money
    yandex_wallet = yandex_access['yandex_wallet']
    yandex_client_id = yandex_access['yandex_client_id']
    yandex_auth_success_uri = yandex_access['yandex_auth_success_uri']
    yandex_auth_fail_uri = yandex_access['yandex_auth_fail_uri']
    yandex_instance_id_key = methods.get_yandex_instance_id_key(yandex_client_id)

    # создаем обьект платежного клиента
    try:
        external_payment = ExternalPayment(yandex_instance_id_key)
    except:
        return

    try:
        payment_request_id = methods.external_payment_request(external_payment,
                                                              yandex_instance_id_key,
                                                              yandex_wallet,
                                                              amount,
                                                              message=None)
    except:
        return
    if payment_request_id is None:
        return

    try:
        response_external_payment_process = methods.external_payment_process(external_payment,
                                                                             payment_request_id,
                                                                             yandex_auth_success_uri,
                                                                             yandex_auth_fail_uri,
                                                                             yandex_client_id,
                                                                             request_token=False)
    except:
        return
    if response_external_payment_process["key"] is not "access_pay":
        return
    redirect_url_for_access_pay = response_external_payment_process["value"]

    return redirect_url_for_access_pay, payment_request_id, yandex_instance_id_key


# проверка статуса транзакции
def check_status(yandex_client_id, yandex_instance_id_key, payment_request_id,
                 yandex_auth_success_uri, yandex_auth_fail_uri):

    external_payment = ExternalPayment(yandex_instance_id_key)

    response_external_payment_process = methods.external_payment_process(external_payment,
                                                                         payment_request_id,
                                                                         yandex_auth_success_uri,
                                                                         yandex_auth_fail_uri,
                                                                         yandex_client_id,
                                                                         request_token=False)
    if response_external_payment_process["key"] is "status":
        return response_external_payment_process
    else:
        return
