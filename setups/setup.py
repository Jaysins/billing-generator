import pkgutil
import setups
import sys
from sendbox_payments.services.core import *
from sendbox_payments.services.payments import *
from sendbox_payments.services.apps import *
thismodule = sys.modules[__name__]


def core_setup(filenames=None):
    importer_ = None
    all_modules = []

    # get all setup files in the setups package
    for importer, modname, ispkg in pkgutil.iter_modules(setups.__path__):
        importer_ = importer
        all_modules.append(modname)

    # choose which set of files to run depending on user specification
    if not filenames:
        filenames = all_modules

    # exclude this module if among the files specified as it is an execution file
    if filenames.count(thismodule.__name__.split('.')[-1]) > 0:
        filenames.remove(thismodule.__name__.split('.')[-1])

    for name in filenames:
        print(name)
        module = importer_.find_module(name).load_module(name)
        print(module, "===module====")
        if module:
            service_name = module.obj.get("klass")
            data = module.obj.get("data")
            pk = module.obj.get("pk", "_id")
            is_pk = module.obj.get("is_pk", True)
            method_name = module.obj.get("method", "None")
            service = getattr(thismodule, service_name)
            # service.objects.delete()
            for d in data:
                if is_pk:
                    try:
                        obj_ = service.get(d[pk])
                    except ObjectNotFoundException:
                        obj_ = None
                else:
                    obj_ = service.find_one({pk: d[pk]})
                if not obj_:
                    print("creating=====", d[pk])
                    method = getattr(service, method_name, None)
                    if method:
                        method(**d)
                    else:
                        service.create(**d)
