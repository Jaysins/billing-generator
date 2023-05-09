from sendbox_payments.services.payments import *
from sendbox_payments.services.core import *
from pytest import fixture, mark
from setups.setup import core_setup

connect(settings.TEST_DATABASE_URL, connect=False, maxPoolSize=None)

@fixture()
def service():
    return ProfileService


@fixture()
def reboot_():
    TransactionService.objects.delete()


@mark.unit
def test_charge_with_positive_balance(reboot_, get_obj, debit_data):
    """

    :return:
    """
    app = ApplicationService.objects.first()
    old_bal = app.get_charge_account().balance
    profile = get_obj
    acc = profile.get_charge_account()
    acc = AccountService.update(acc.pk, balance=acc.balance+1000)
    AccountService.charge(1000, acc.key, app.pk, **debit_data)
    app = ApplicationService.get(app.pk)
    new_bal = app.get_charge_account().balance
    assert old_bal < new_bal


@mark.unit
@mark.debt
def test_charge_to_make_debt(reboot_, get_obj, debit_data):
    app = ApplicationService.objects.first()
    print(app.name)
    old_bal = app.get_charge_account().balance
    profile = get_obj
    print(profile.name)
    acc = profile.get_charge_account()
    acc = AccountService.update(acc.pk, balance=1000)
    AccountService.charge(1100, acc.key, app.pk, allow_negative=True, **debit_data)
    app = ApplicationService.get(app.pk)
    new_bal = app.get_charge_account().balance
    assert new_bal - old_bal == 1000
