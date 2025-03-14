import time
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs


if __name__ == "__main__":
    container = DockerContainer("typesense/typesense:28.0")
    container.with_exposed_ports(8108)
    container.with_command("--data-dir /etc --api-key=123abc --enable-cors")
    container.start()
    wait_for_logs(container, "Starting Typesense")

    ip = container.get_container_host_ip()
    port = container.get_exposed_port(8108)

    print("\n\033[94mTypesense container setup and running. Use \033[93mCTRL-C\033[94m to cleanly shut it down.\033[0m")
    print(f"\033[94mTest container is online with:\033[0m")
    print(f"curl http://{ip}:{port}/health")
    print("\033[92mSet the follow environment variables to access it:\033[0m")
    print(f"export PyST_typesense_url=\"http://{ip}:{port}\"")
    print(f"export PyST_typesense_api_key=\"123abc\"")

    while True:
        try:
            time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n\033[93mShutting down the container\n\033[94m")
            container.stop()
            break
