import grpc
from concurrent import futures
import time

# from app import <rcp_client>

# from app.grpc_.services.<module> import <Resource>

import settings

server = grpc.server(futures.ThreadPoolExecutor(max_workers=int(settings.GRPC_MAX_THREAD_WORKERS)),
                     maximum_concurrent_rpcs=int(settings.GRPC_MAX_CONC_RPC))

# use the generated function `add_UserSignupServicer_to_server`
# to add the defined class to the server

# <rcp_client>.add_service.add_ProfileServicer_to_server(ProfileServiceResource(), server)


print('Sendbox Payments GRPC Service.\nListening on port {}\n============'.format(settings.GRPC_SERVER_PORT))
server.add_insecure_port('[::]:{}'.format(settings.GRPC_SERVER_PORT))
server.start()

try:
    while True:
        time.sleep(settings.GRPC_SERVER_SLEEP_TIME)
except KeyboardInterrupt:
    server.stop(0)
