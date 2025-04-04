import time

from testcontainers.postgres import PostgresContainer

# See also https://www.docker.com/blog/how-to-use-the-postgres-docker-official-image/


if __name__ == "__main__":
    postgres = PostgresContainer("postgres:16")
    postgres.start()

    # Print log messages here instead of below
    ip = postgres.get_container_host_ip()
    port = postgres.get_exposed_port(5432)

    print(
        "\n\033[94mPostgres container setup and running. Use \033[93mCTRL-C\033[94m to cleanly shut it down.\033[0m"
    )
    print("\033[92mSet the follow environment variables to access it:\033[0m")
    print('export PyST_db_backend="postgres"')
    print(f'export PyST_db_user="{postgres.username}"')
    print(f'export PyST_db_pass="{postgres.password}"')
    print(f'export PyST_db_host="{ip}"')
    print(f'export PyST_db_port="{port}"')
    print(f'export PyST_db_name="{postgres.dbname}"')

    while True:
        try:
            time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n\033[93mShutting down the container\n\033[94m")
            postgres.stop()
            break
