
import time
from dependency_map import DEPENDENCIES

restored = set()

def restore_service(service):

    if service in restored:
        return

    dependencies = DEPENDENCIES[service]

    for dep in dependencies:
        restore_service(dep)

    print(f"[+] Restoring {service}...")
    time.sleep(2)

    print(f"[OK] {service} restored")

    restored.add(service)


def start_recovery():
    for service in DEPENDENCIES:
        restore_service(service)


if __name__ == "__main__":
    start_recovery()